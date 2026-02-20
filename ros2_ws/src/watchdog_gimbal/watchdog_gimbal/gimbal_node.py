"""ROS2 узел управления подвесом SIYI A8 mini.

Протокол: MAVLink Gimbal Protocol v2 (через MAVROS).
Режимы:
  - MANUAL: ручное управление каналами RC (ch7=tilt, ch8=pan)
  - TRACK:  автослежение за целью из /detection/tracks
  - NEUTRAL: возврат в нейтраль (pitch=0, yaw=0)

Топики:
  Подписки:
    /detection/tracks       — треки от watchdog_detection (TRACK режим)
    /rc/gimbal_cmd          — [tilt, pan] от RC интерфейса [-1..1]
  Публикации:
    /mavros/mount_control/command  — MAVLink MOUNT_CONTROL (v1 compat.)
    /gimbal/status          — текущий статус
"""

import math

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import MountControl
from std_msgs.msg import String, Float32MultiArray

try:
    from watchdog_msgs.msg import DetectionArray

    CUSTOM_MSGS = True
except ImportError:
    CUSTOM_MSGS = False


class GimbalNode(Node):
    """Управление SIYI A8 mini через MAVLink Gimbal Protocol v2."""

    MODE_NEUTRAL = "neutral"
    MODE_MANUAL = "manual"
    MODE_TRACK = "track"

    # Пределы SIYI A8 mini
    PITCH_MIN = -90.0  # градусы (вниз)
    PITCH_MAX = 25.0  # градусы (вверх)
    YAW_MIN = -160.0
    YAW_MAX = 160.0

    def __init__(self):
        super().__init__("gimbal_node")

        self.declare_parameter("pitch_min", self.PITCH_MIN)
        self.declare_parameter("pitch_max", self.PITCH_MAX)
        self.declare_parameter("yaw_min", self.YAW_MIN)
        self.declare_parameter("yaw_max", self.YAW_MAX)
        # Чувствительность ручного управления (°/с при полном отклонении стика)
        self.declare_parameter("manual_rate_deg_s", 60.0)
        # Пропорциональный коэффициент для автослежения
        self.declare_parameter("track_kp_pitch", 0.08)
        self.declare_parameter("track_kp_yaw", 0.08)
        # Размер изображения камеры (для вычисления ошибки центрирования)
        self.declare_parameter("camera_width", 3840)
        self.declare_parameter("camera_height", 2160)
        # ID класса приоритетной цели (0=person)
        self.declare_parameter("track_target_class", 0)

        self.pitch_min = self.get_parameter("pitch_min").value
        self.pitch_max = self.get_parameter("pitch_max").value
        self.yaw_min = self.get_parameter("yaw_min").value
        self.yaw_max = self.get_parameter("yaw_max").value
        self.manual_rate = self.get_parameter("manual_rate_deg_s").value
        self.kp_pitch = self.get_parameter("track_kp_pitch").value
        self.kp_yaw = self.get_parameter("track_kp_yaw").value
        self.cam_w = self.get_parameter("camera_width").value
        self.cam_h = self.get_parameter("camera_height").value
        self.target_class = self.get_parameter("track_target_class").value

        # Состояние
        self.mode = self.MODE_NEUTRAL
        self.current_pitch = 0.0  # градусы
        self.current_yaw = 0.0
        self.rc_tilt = 0.0  # нормализованное [-1..1]
        self.rc_pan = 0.0
        self.target_track_id: int | None = None

        # Публикации
        self.mount_pub = self.create_publisher(MountControl, "/mavros/mount_control/command", 10)
        self.status_pub = self.create_publisher(String, "/gimbal/status", 10)

        # Подписки
        self.rc_gimbal_sub = self.create_subscription(Float32MultiArray, "/rc/gimbal_cmd", self._rc_gimbal_callback, 10)
        if CUSTOM_MSGS:
            self.tracks_sub = self.create_subscription(DetectionArray, "/detection/tracks", self._tracks_callback, 5)

        # Управляющий цикл 20 Hz
        self.create_timer(0.05, self._control_loop)

        self.get_logger().info(
            f"GimbalNode (SIYI A8 mini) запущен | "
            f"pitch=[{self.pitch_min},{self.pitch_max}]° | "
            f"yaw=[{self.yaw_min},{self.yaw_max}]°"
        )

    def _rc_gimbal_callback(self, msg: Float32MultiArray):
        """Обновляет RC sticks значения и переключается в MANUAL режим."""
        if len(msg.data) >= 2:
            self.rc_tilt = float(msg.data[0])
            self.rc_pan = float(msg.data[1])
            # Если стик двигают — приоритет MANUAL над TRACK
            if abs(self.rc_tilt) > 0.05 or abs(self.rc_pan) > 0.05:
                self.mode = self.MODE_MANUAL
            elif self.mode == self.MODE_MANUAL:
                # Стики в нейтрали → обратно в TRACK если были треки
                self.mode = self.MODE_TRACK

    def _tracks_callback(self, msg):
        """Обновляет цель для автослежения."""
        if not CUSTOM_MSGS or self.mode == self.MODE_MANUAL:
            return
        if not msg.detections:
            return

        # Выбираем цель: предпочитаем track_target_class, потом любой трек
        target = None
        for det in msg.detections:
            if det.class_id == self.target_class:
                if target is None or det.track_id == self.target_track_id:
                    target = det

        if target is None:
            target = msg.detections[0]  # Берём первый доступный трек

        self.target_track_id = target.track_id

        # Вычисляем ошибку центрирования (в нормализованных координатах)
        err_x = (target.cx - self.cam_w / 2) / (self.cam_w / 2)  # [-1..1]
        err_y = (target.cy - self.cam_h / 2) / (self.cam_h / 2)  # [-1..1]

        # Пропорциональная коррекция позиции подвеса
        d_pitch = -err_y * self.kp_pitch * 90.0  # Инвертируем Y
        d_yaw = err_x * self.kp_yaw * 90.0

        self.current_pitch = self._clamp(self.current_pitch + d_pitch, self.pitch_min, self.pitch_max)
        self.current_yaw = self._clamp(self.current_yaw + d_yaw, self.yaw_min, self.yaw_max)
        self.mode = self.MODE_TRACK

    def _control_loop(self):
        """20 Hz цикл управления — публикует команду подвеса."""
        dt = 0.05  # 1/20 Hz

        if self.mode == self.MODE_MANUAL:
            self.current_pitch = self._clamp(
                self.current_pitch + self.rc_tilt * self.manual_rate * dt, self.pitch_min, self.pitch_max
            )
            self.current_yaw = self._clamp(
                self.current_yaw + self.rc_pan * self.manual_rate * dt, self.yaw_min, self.yaw_max
            )

        elif self.mode == self.MODE_NEUTRAL:
            # Плавный возврат в нейтраль
            self.current_pitch += (0.0 - self.current_pitch) * 0.1
            self.current_yaw += (0.0 - self.current_yaw) * 0.1

        # Отправляем команду через MAVROS MountControl
        self._send_mount_command(self.current_pitch, self.current_yaw, 0.0)

        # Публикуем статус
        status = String()
        status.data = (
            f"mode={self.mode}|pitch={self.current_pitch:.1f}°"
            f"|yaw={self.current_yaw:.1f}°"
            f"|track_id={self.target_track_id}"
        )
        self.status_pub.publish(status)

    def _send_mount_command(self, pitch_deg: float, yaw_deg: float, roll_deg: float):
        """Публикует MAVLink MOUNT_CONTROL команду через MAVROS."""
        msg = MountControl()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.mode = 2  # MAV_MOUNT_MODE_MAVLINK_TARGETING
        msg.pitch = math.radians(pitch_deg)  # MAVROS ожидает радианы
        msg.yaw = math.radians(yaw_deg)
        msg.roll = math.radians(roll_deg)
        self.mount_pub.publish(msg)

    @staticmethod
    def _clamp(value: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, value))

    def set_mode(self, mode: str):
        """Внешняя установка режима ('neutral'/'manual'/'track')."""
        if mode in (self.MODE_NEUTRAL, self.MODE_MANUAL, self.MODE_TRACK):
            self.mode = mode
            self.get_logger().info(f"Gimbal mode → {mode}")


def main(args=None):
    rclpy.init(args=args)
    node = GimbalNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
