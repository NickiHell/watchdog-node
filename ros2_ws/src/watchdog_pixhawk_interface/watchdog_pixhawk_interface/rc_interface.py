"""Модуль обработки RC команд — RadioMaster TX16 + ELRS 900 МГц → SBUS → Pixhawk 4.

Маппинг каналов TX16 (ELRS, 8 каналов):
  Ch1: Roll (крен)
  Ch2: Pitch (тангаж)
  Ch3: Throttle (газ)
  Ch4: Yaw (рыскание)
  Ch5: ARM (двигатели) — выше 1800 = ARM
  Ch6: Flight Mode (Stabilize / Loiter / Auto)
  Ch7: Gimbal Tilt (наклон подвеса)
  Ch8: Gimbal Pan (поворот подвеса)
"""

import rclpy
from rclpy.node import Node
from mavros_msgs.msg import RCIn
from geometry_msgs.msg import Twist
from std_msgs.msg import String, Float32MultiArray


class RCInterface(Node):
    """Обработчик команд от TX16 ELRS."""

    CH_ROLL = 0  # индекс 0 = канал 1
    CH_PITCH = 1
    CH_THROTTLE = 2
    CH_YAW = 3
    CH_ARM = 4  # канал 5
    CH_FLIGHT_MODE = 5  # канал 6
    CH_GIMBAL_TILT = 6  # канал 7
    CH_GIMBAL_PAN = 7  # канал 8

    REQUIRED_CHANNELS = 8

    def __init__(self):
        super().__init__("rc_interface")

        self.declare_parameter("rc_enabled", True)
        self.declare_parameter("rc_override_threshold", 1500)
        self.declare_parameter("rc_deadzone", 50)
        self.declare_parameter("max_velocity", 5.0)
        self.declare_parameter("max_vertical_velocity", 2.0)
        self.declare_parameter("max_angular_velocity", 1.5)
        self.declare_parameter("arm_threshold", 1800)
        # Пороги Flight Mode (PWM): stabilize<1300, loiter<1600, auto=1900
        self.declare_parameter("flight_mode_stabilize", 1300)
        self.declare_parameter("flight_mode_loiter", 1600)

        self.rc_enabled = self.get_parameter("rc_enabled").value
        self.neutral = self.get_parameter("rc_override_threshold").value
        self.deadzone = self.get_parameter("rc_deadzone").value
        self.max_vel = self.get_parameter("max_velocity").value
        self.max_vert_vel = self.get_parameter("max_vertical_velocity").value
        self.max_ang_vel = self.get_parameter("max_angular_velocity").value
        self.arm_threshold = self.get_parameter("arm_threshold").value
        self.fm_stabilize = self.get_parameter("flight_mode_stabilize").value
        self.fm_loiter = self.get_parameter("flight_mode_loiter").value

        self.last_rc: RCIn | None = None
        self.rc_active = False
        self.armed = False
        self.flight_mode = "stabilize"

        # Подписчики
        self.rc_sub = self.create_subscription(RCIn, "/mavros/rc/in", self._rc_callback, 10)

        # Издатели
        self.cmd_vel_pub = self.create_publisher(Twist, "/rc/cmd_vel", 10)
        self.status_pub = self.create_publisher(String, "/rc/status", 10)
        # Команды подвеса [tilt_normalized (-1..1), pan_normalized (-1..1)]
        self.gimbal_cmd_pub = self.create_publisher(Float32MultiArray, "/rc/gimbal_cmd", 10)
        # Статус ARM для других узлов
        self.arm_pub = self.create_publisher(String, "/rc/arm_status", 10)

        self.create_timer(0.05, self._timer_callback)  # 20 Hz

        self.get_logger().info("RC Interface (TX16 ELRS, 8 каналов) запущен")

    def _rc_callback(self, msg: RCIn):
        self.last_rc = msg
        if len(msg.channels) >= 4:
            self.rc_active = all(900 <= ch <= 2100 for ch in msg.channels[:4])
        else:
            self.rc_active = False

    def _timer_callback(self):
        if not self.rc_enabled or not self.last_rc or not self.rc_active:
            self._publish_status("rc_inactive")
            return

        ch = self.last_rc.channels

        # ARM (ch5)
        if len(ch) > self.CH_ARM:
            self.armed = ch[self.CH_ARM] > self.arm_threshold

        # Flight Mode (ch6)
        if len(ch) > self.CH_FLIGHT_MODE:
            fm_pwm = ch[self.CH_FLIGHT_MODE]
            if fm_pwm < self.fm_stabilize:
                self.flight_mode = "stabilize"
            elif fm_pwm < self.fm_loiter:
                self.flight_mode = "loiter"
            else:
                self.flight_mode = "auto"

        # Публикуем ARM статус
        arm_msg = String()
        arm_msg.data = "armed" if self.armed else "disarmed"
        self.arm_pub.publish(arm_msg)

        # Cmd_vel (Roll/Pitch/Throttle/Yaw)
        roll = self._normalize(ch[self.CH_ROLL])
        pitch = self._normalize(ch[self.CH_PITCH])
        throttle = self._normalize(ch[self.CH_THROTTLE])
        yaw = self._normalize(ch[self.CH_YAW])

        cmd = Twist()
        cmd.linear.x = self._deadzone(pitch) * self.max_vel
        cmd.linear.y = self._deadzone(roll) * self.max_vel
        cmd.linear.z = self._deadzone(throttle) * self.max_vert_vel
        cmd.angular.z = self._deadzone(yaw) * self.max_ang_vel
        self.cmd_vel_pub.publish(cmd)

        # Gimbal (ch7 = tilt, ch8 = pan)
        if len(ch) > self.CH_GIMBAL_PAN:
            gimbal_msg = Float32MultiArray()
            gimbal_msg.data = [
                float(self._deadzone(self._normalize(ch[self.CH_GIMBAL_TILT]))),
                float(self._deadzone(self._normalize(ch[self.CH_GIMBAL_PAN]))),
            ]
            self.gimbal_cmd_pub.publish(gimbal_msg)

        self._publish_status(
            f"rc_active|arm={arm_msg.data}|mode={self.flight_mode}"
            f"|roll={roll:.2f}|pitch={pitch:.2f}"
            f"|thr={throttle:.2f}|yaw={yaw:.2f}"
        )

    def _normalize(self, pwm: int) -> float:
        """Нормализует PWM (1000-2000) в [-1.0, 1.0]."""
        if pwm < self.neutral:
            v = -(self.neutral - pwm) / (self.neutral - 1000)
        else:
            v = (pwm - self.neutral) / (2000 - self.neutral)
        return max(-1.0, min(1.0, v))

    def _deadzone(self, value: float) -> float:
        """Применяет мёртвую зону и перемасштабирует."""
        dz = self.deadzone / (self.neutral - 1000)
        if abs(value) < dz:
            return 0.0
        sign = 1.0 if value > 0 else -1.0
        return sign * (abs(value) - dz) / (1.0 - dz)

    def _publish_status(self, text: str):
        msg = String()
        msg.data = text
        self.status_pub.publish(msg)

    def is_rc_active(self) -> bool:
        return self.rc_active

    def is_armed(self) -> bool:
        return self.armed

    def get_flight_mode(self) -> str:
        return self.flight_mode


def main(args=None):
    rclpy.init(args=args)
    node = RCInterface()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
