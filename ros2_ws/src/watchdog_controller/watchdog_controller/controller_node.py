"""Main controller node for WatchDog drone.

This node coordinates all subsystems:
- 3D navigation and path planning
- Camera and detection (YOLOv8n + ByteTrack)
- Target tracking
- Flight control
- Obstacle avoidance
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String, Header
import time
import os
import math

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from watchdog_controller.state_machine import StateMachine, RobotMode

# Используем кастомные сообщения если доступны, иначе заглушки
try:
    from watchdog_msgs.msg import ControllerState, DetectionArray, RobotStatus

    CUSTOM_MSGS_AVAILABLE = True
except ImportError:
    CUSTOM_MSGS_AVAILABLE = False
    # Заглушки для разработки
    ControllerState = String
    DetectionArray = String
    RobotStatus = String


class ControllerNode(Node):
    """Main controller node."""

    def __init__(self):
        super().__init__("controller_node")

        # Parameters
        self.declare_parameter("default_mode", "idle")
        self.declare_parameter("update_rate", 10.0)  # Hz
        self.declare_parameter("emergency_stop_distance", 0.2)  # meters
        self.declare_parameter("safety.min_distance_to_person", 1.0)  # meters
        self.declare_parameter("safety.person_detection_safety_enabled", True)

        default_mode_str = self.get_parameter("default_mode").get_parameter_value().string_value
        update_rate = self.get_parameter("update_rate").get_parameter_value().double_value
        self.emergency_stop_distance = self.get_parameter("emergency_stop_distance").get_parameter_value().double_value
        self.min_distance_to_person = (
            self.get_parameter("safety.min_distance_to_person").get_parameter_value().double_value
        )
        self.person_safety_enabled = (
            self.get_parameter("safety.person_detection_safety_enabled").get_parameter_value().bool_value
        )

        # State machine
        try:
            initial_mode = RobotMode(default_mode_str)
        except ValueError:
            self.get_logger().warn(f"Неизвестный режим: {default_mode_str}, используем IDLE")
            initial_mode = RobotMode.IDLE

        self.state_machine = StateMachine(initial_mode=initial_mode)
        self.state_machine.register_mode_change_callback(self._on_mode_change)

        # Состояние системы
        self.subsystem_status = {
            "lidar": False,
            "camera": False,
            "detection": False,
            "navigation": False,
            "pixhawk": False,
            "rc": False,
        }

        self.last_lidar_scan: LaserScan = None
        self.last_detections: DetectionArray = None
        self.battery_level = 100
        self.start_time = time.time()

        # Кэш для метрик системы
        self._last_cpu_times = None
        self._last_cpu_time = None

        # QoS профили
        qos_sensor = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        qos_control = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", qos_control)
        if CUSTOM_MSGS_AVAILABLE:
            self.state_pub = self.create_publisher(ControllerState, "/controller/state", qos_control)
            self.status_pub = self.create_publisher(RobotStatus, "/drone/status", qos_control)
        else:
            self.state_pub = self.create_publisher(String, "/controller/state", qos_control)
            self.status_pub = self.create_publisher(String, "/drone/status", qos_control)

        # Subscribers
        self.lidar_sub = self.create_subscription(LaserScan, "/sensor/lidar/scan", self.lidar_callback, qos_sensor)
        self.detection_sub = self.create_subscription(
            DetectionArray if CUSTOM_MSGS_AVAILABLE else String,
            "/detection/tracks",
            self.detection_callback,
            qos_sensor,
        )
        self.nav_goal_sub = self.create_subscription(PoseStamped, "/navigation/goal", self.nav_goal_callback, 10)

        # Service для изменения режима (можно добавить позже)
        # self.mode_service = self.create_service(SetMode, '/controller/set_mode', self.set_mode_callback)

        # Timer for state updates
        self.create_timer(1.0 / update_rate, self.update_loop)
        self.create_timer(1.0, self.status_update_loop)  # Статус раз в секунду

        self.get_logger().info(f"Controller node started in {self.state_machine.get_mode().value} mode")

    def _get_min_valid_lidar_distance(self, scan: LaserScan) -> float:
        """Получает минимальное валидное расстояние от лидара.

        Args:
            scan: Сообщение LaserScan

        Returns:
            Минимальное валидное расстояние или float('inf') если нет валидных значений
        """
        if not scan or not scan.ranges:
            return float("inf")

        valid_ranges = []
        for r in scan.ranges:
            # Проверяем на валидность: не NaN, не Inf, в пределах range_min и range_max
            if math.isfinite(r) and r >= scan.range_min and r <= scan.range_max:
                valid_ranges.append(r)

        if not valid_ranges:
            return float("inf")

        return min(valid_ranges)

    def _on_mode_change(self, from_mode: RobotMode, to_mode: RobotMode):
        """Callback при изменении режима.

        Args:
            from_mode: Предыдущий режим
            to_mode: Новый режим
        """
        self.get_logger().info(f"Mode changed: {from_mode.value} -> {to_mode.value}")

        # Останавливаем движение при переходе в режим ошибки или аварийной остановки
        if to_mode in [RobotMode.ERROR, RobotMode.EMERGENCY_STOP]:
            self._emergency_stop()

    def lidar_callback(self, msg: LaserScan):
        """Callback для данных лидара.

        Args:
            msg: Сообщение LaserScan
        """
        self.last_lidar_scan = msg
        self.subsystem_status["lidar"] = True

        # Проверка на препятствия для аварийной остановки
        if self.state_machine.get_mode() not in [RobotMode.EMERGENCY_STOP, RobotMode.ERROR]:
            min_distance = self._get_min_valid_lidar_distance(msg)
            if min_distance < self.emergency_stop_distance:
                self.get_logger().warning(f"Препятствие слишком близко: {min_distance:.2f}m, аварийная остановка!")
                self.state_machine.transition_to(RobotMode.EMERGENCY_STOP)

    def detection_callback(self, msg):
        """Callback для треков детекции (YOLOv8n + ByteTrack).

        Args:
            msg: Сообщение DetectionArray или String
        """
        self.last_detections = msg
        self.subsystem_status["detection"] = True

        # Проверка безопасности: если объекты обнаружены, проверяем расстояние
        objects_detected = False
        if CUSTOM_MSGS_AVAILABLE and hasattr(msg, "detections") and len(msg.detections) > 0:
            objects_detected = True

            # Если включена безопасность и есть данные лидара, проверяем расстояние
            if self.person_safety_enabled and self.last_lidar_scan:
                min_distance = self._get_min_valid_lidar_distance(self.last_lidar_scan)
                if min_distance < self.min_distance_to_person:
                    self.get_logger().warning(
                        f"БЕЗОПАСНОСТЬ: Объект слишком близко ({min_distance:.2f}m), "
                        f"требуется минимум {self.min_distance_to_person:.2f}m!"
                    )
                    if self.state_machine.can_transition_to(RobotMode.EMERGENCY_STOP):
                        self.state_machine.transition_to(RobotMode.EMERGENCY_STOP)

        # Переход в режим отслеживания при обнаружении объектов в режиме IDLE
        if (
            self.state_machine.get_mode() == RobotMode.IDLE
            and objects_detected
            and self.state_machine.can_transition_to(RobotMode.TRACKING)
        ):
            self.state_machine.transition_to(RobotMode.TRACKING)

    def nav_goal_callback(self, msg: PoseStamped):
        """Callback для цели навигации.

        Args:
            msg: Целевая позиция
        """
        if self.state_machine.can_transition_to(RobotMode.NAVIGATION):
            self.state_machine.transition_to(RobotMode.NAVIGATION)
            self.get_logger().info(f"Received navigation goal: {msg.pose.position}")

    def update_loop(self):
        """Main update loop."""
        current_mode = self.state_machine.get_mode()

        if current_mode == RobotMode.IDLE:
            self._handle_idle_mode()
        elif current_mode == RobotMode.TAKEOFF:
            self._handle_takeoff_mode()
        elif current_mode == RobotMode.NAVIGATION:
            self._handle_navigation_mode()
        elif current_mode == RobotMode.TRACKING:
            self._handle_tracking_mode()
        elif current_mode == RobotMode.HOVERING:
            self._handle_hovering_mode()
        elif current_mode == RobotMode.LANDING:
            self._handle_landing_mode()
        elif current_mode == RobotMode.ERROR:
            self._handle_error_mode()
        elif current_mode == RobotMode.EMERGENCY_STOP:
            self._handle_emergency_stop_mode()

        # Публикуем состояние
        self._publish_state()

    def _handle_idle_mode(self):
        """Обработка режима IDLE."""
        # Останавливаем движение
        self._stop_movement()

    def _handle_navigation_mode(self):
        """Обработка режима навигации."""
        # Навигация обрабатывается узлом navigation_node
        # Контроллер только отслеживает статус

    def _handle_takeoff_mode(self):
        """Обработка режима взлета."""
        # Взлет обрабатывается узлом navigation_node
        # Контроллер отслеживает статус

    def _handle_tracking_mode(self):
        """Обработка режима отслеживания."""
        # Отслеживание обрабатывается соответствующими узлами
        # Контроллер координирует их работу

        # Проверка безопасности: поддерживаем минимальное расстояние до людей
        if self.person_safety_enabled and self.last_lidar_scan:
            min_distance = self._get_min_valid_lidar_distance(self.last_lidar_scan)
            if min_distance < self.min_distance_to_person:
                # Человек слишком близко - останавливаемся или отдаляемся
                self.get_logger().warning(
                    f"БЕЗОПАСНОСТЬ: Поддерживаем расстояние {self.min_distance_to_person:.2f}m от человека"
                )
                # Останавливаем движение вперед
                cmd = Twist()
                cmd.linear.x = -0.2  # Отдаляемся медленно
                cmd.linear.y = 0.0
                cmd.linear.z = 0.0
                cmd.angular.z = 0.0
                self.cmd_vel_pub.publish(cmd)

    def _handle_hovering_mode(self):
        """Обработка режима зависания."""
        # Зависание обрабатывается узлом navigation_node
        # Контроллер отслеживает статус

    def _handle_landing_mode(self):
        """Обработка режима посадки."""
        # Посадка обрабатывается узлом navigation_node
        # Контроллер отслеживает статус

    def _handle_error_mode(self):
        """Обработка режима ошибки."""
        self._stop_movement()

        # Попытка восстановления после таймаута
        # Можно добавить логику автоматического восстановления

    def _handle_emergency_stop_mode(self):
        """Обработка режима аварийной остановки."""
        self._emergency_stop()

        # После проверки препятствий можно перейти в IDLE
        if self.last_lidar_scan:
            min_distance = self._get_min_valid_lidar_distance(self.last_lidar_scan)
            if min_distance > self.emergency_stop_distance * 1.5:
                if self.state_machine.can_transition_to(RobotMode.IDLE):
                    self.state_machine.transition_to(RobotMode.IDLE)

    def _stop_movement(self):
        """Останавливает движение дрона."""
        cmd = Twist()
        self.cmd_vel_pub.publish(cmd)

    def _emergency_stop(self):
        """Аварийная остановка."""
        self._stop_movement()
        self.get_logger().error("EMERGENCY STOP ACTIVATED!")

    def _publish_state(self):
        """Публикует состояние контроллера."""
        if CUSTOM_MSGS_AVAILABLE:
            state = ControllerState()
            state.header = Header()
            state.header.stamp = self.get_clock().now().to_msg()
            state.header.frame_id = "base_link"
            state.mode = self.state_machine.get_mode().value
            state.lidar_active = self.subsystem_status["lidar"]
            state.camera_active = self.subsystem_status["camera"]
            state.detection_active = self.subsystem_status["detection"]
            state.navigation_active = self.subsystem_status["navigation"]
            state.pixhawk_connected = self.subsystem_status["pixhawk"]
            state.rc_active = self.subsystem_status["rc"]
            state.battery_level = self.battery_level
            state.uptime = time.time() - self.start_time
            state.status_message = f"Running in {self.state_machine.get_mode().value} mode"
            self.state_pub.publish(state)
        else:
            # Fallback на String
            msg = String()
            msg.data = f"Mode: {self.state_machine.get_mode().value}"
            self.state_pub.publish(msg)

    def status_update_loop(self):
        """Периодическое обновление статуса."""
        # Проверка таймаутов подсистем
        # Если подсистема не отвечает, отмечаем как неактивную
        # (можно добавить более сложную логику)

        # Публикация общего статуса
        if CUSTOM_MSGS_AVAILABLE:
            status = RobotStatus()
            status.header = Header()
            status.header.stamp = self.get_clock().now().to_msg()
            status.header.frame_id = "base_link"

            # Определяем системный статус
            if self.state_machine.get_mode() == RobotMode.EMERGENCY_STOP:
                status.system_status = "emergency_stop"
            elif self.state_machine.get_mode() == RobotMode.ERROR:
                status.system_status = "error"
            elif any(not active for active in self.subsystem_status.values()):
                status.system_status = "warning"
            else:
                status.system_status = "operational"

            # Получаем реальные метрики системы
            status.cpu_temperature = self._get_cpu_temperature()
            status.memory_usage = self._get_memory_usage()
            status.cpu_usage = self._get_cpu_usage()

            # Используем состояние контроллера
            if hasattr(self, "state_pub"):
                # Можно создать ControllerState здесь
                pass

            status.error_message = ""
            self.status_pub.publish(status)

    def _get_cpu_temperature(self) -> float:
        """Получает температуру CPU в градусах Цельсия.

        Returns:
            Температура CPU в градусах Цельсия, или 0.0 если недоступна
        """
        if PSUTIL_AVAILABLE:
            try:
                # Пытаемся получить температуру через psutil (требует psutil >= 5.6.0)
                temps = psutil.sensors_temperatures()
                if temps:
                    # Ищем температуру CPU
                    for name, entries in temps.items():
                        if "cpu" in name.lower() or "core" in name.lower():
                            if entries:
                                return entries[0].current
                    # Если не нашли CPU, берем первую доступную температуру
                    for entries in temps.values():
                        if entries:
                            return entries[0].current
            except (AttributeError, OSError, FileNotFoundError):
                pass

        # Fallback: чтение напрямую из /sys (для Raspberry Pi и Linux)
        try:
            thermal_paths = [
                "/sys/class/thermal/thermal_zone0/temp",  # Raspberry Pi
                "/sys/devices/virtual/thermal/thermal_zone0/temp",  # Общий Linux
            ]
            for path in thermal_paths:
                if os.path.exists(path):
                    with open(path) as f:
                        temp_millidegrees = int(f.read().strip())
                        return temp_millidegrees / 1000.0  # Конвертируем в градусы
        except (OSError, ValueError, FileNotFoundError):
            pass

        return 0.0

    def _get_memory_usage(self) -> float:
        """Получает использование памяти в процентах.

        Returns:
            Использование памяти в процентах (0-100), или 0.0 если недоступно
        """
        if PSUTIL_AVAILABLE:
            try:
                memory = psutil.virtual_memory()
                return memory.percent
            except (OSError, AttributeError):
                pass

        # Fallback: чтение из /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split()
                    if len(parts) >= 2:
                        key = parts[0].rstrip(":")
                        value = int(parts[1])
                        meminfo[key] = value

                if "MemTotal" in meminfo and "MemAvailable" in meminfo:
                    mem_total = meminfo["MemTotal"]
                    mem_available = meminfo["MemAvailable"]
                    mem_used = mem_total - mem_available
                    return (mem_used / mem_total) * 100.0
        except (OSError, ValueError, KeyError, FileNotFoundError):
            pass

        return 0.0

    def _get_cpu_usage(self) -> float:
        """Получает использование CPU в процентах.

        Returns:
            Использование CPU в процентах (0-100), или 0.0 если недоступно
        """
        if PSUTIL_AVAILABLE:
            try:
                # Для первого вызова нужен интервал, для последующих можно None
                if self._last_cpu_time is None:
                    return psutil.cpu_percent(interval=0.1)
                return psutil.cpu_percent(interval=None)
            except (OSError, AttributeError):
                pass

        # Fallback: чтение из /proc/stat
        try:
            with open("/proc/stat") as f:
                line = f.readline()
                if line.startswith("cpu "):
                    parts = line.split()
                    # Формат: cpu user nice system idle iowait irq softirq
                    if len(parts) >= 5:
                        user = int(parts[1])
                        nice = int(parts[2])
                        system = int(parts[3])
                        idle = int(parts[4])
                        iowait = int(parts[5]) if len(parts) > 5 else 0

                        total = user + nice + system + idle + iowait
                        used = user + nice + system

                        current_time = time.time()
                        if self._last_cpu_times is not None and self._last_cpu_time is not None:
                            time_diff = current_time - self._last_cpu_time
                            if time_diff > 0:
                                total_diff = total - self._last_cpu_times[0]
                                used_diff = used - self._last_cpu_times[1]
                                if total_diff > 0:
                                    cpu_percent = (used_diff / total_diff) * 100.0
                                    self._last_cpu_times = (total, used)
                                    self._last_cpu_time = current_time
                                    return cpu_percent

                        self._last_cpu_times = (total, used)
                        self._last_cpu_time = current_time
        except (OSError, ValueError, IndexError, FileNotFoundError):
            pass

        return 0.0


def main(args=None):
    """Entry point."""
    rclpy.init(args=args)
    node = ControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
