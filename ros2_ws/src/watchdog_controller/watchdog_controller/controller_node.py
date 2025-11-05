"""Main controller node for WatchDog robot.

This node coordinates all subsystems:
- Lidar navigation
- Camera and face detection
- Speech processing
- Beacon tracking
- Movement control
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import LaserScan, Image
from std_msgs.msg import String, Header
import time

from watchdog_controller.state_machine import StateMachine, RobotMode

# Используем кастомные сообщения если доступны, иначе заглушки
try:
    from watchdog_msgs.msg import ControllerState, FaceDetections, RobotStatus
    CUSTOM_MSGS_AVAILABLE = True
except ImportError:
    CUSTOM_MSGS_AVAILABLE = False
    # Заглушки для разработки
    ControllerState = String
    FaceDetections = String
    RobotStatus = String


class ControllerNode(Node):
    """Main controller node."""

    def __init__(self):
        super().__init__('controller_node')

        # Parameters
        self.declare_parameter('default_mode', 'idle')
        self.declare_parameter('update_rate', 10.0)  # Hz
        self.declare_parameter('emergency_stop_distance', 0.2)  # meters

        default_mode_str = self.get_parameter('default_mode').get_parameter_value().string_value
        update_rate = self.get_parameter('update_rate').get_parameter_value().double_value
        self.emergency_stop_distance = (
            self.get_parameter('emergency_stop_distance').get_parameter_value().double_value
        )

        # State machine
        try:
            initial_mode = RobotMode(default_mode_str)
        except ValueError:
            self.get_logger().warn(f'Неизвестный режим: {default_mode_str}, используем IDLE')
            initial_mode = RobotMode.IDLE

        self.state_machine = StateMachine(initial_mode=initial_mode)
        self.state_machine.register_mode_change_callback(self._on_mode_change)

        # Состояние системы
        self.subsystem_status = {
            'lidar': False,
            'camera': False,
            'face_detection': False,
            'speech': False,
            'navigation': False,
            'stm32': False,
        }

        self.last_lidar_scan: LaserScan = None
        self.last_face_detections: FaceDetections = None
        self.battery_level = 100
        self.start_time = time.time()

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
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', qos_control)
        if CUSTOM_MSGS_AVAILABLE:
            self.state_pub = self.create_publisher(ControllerState, '/controller/state', qos_control)
            self.status_pub = self.create_publisher(RobotStatus, '/robot/status', qos_control)
        else:
            self.state_pub = self.create_publisher(String, '/controller/state', qos_control)
            self.status_pub = self.create_publisher(String, '/robot/status', qos_control)

        # Subscribers
        self.lidar_sub = self.create_subscription(
            LaserScan, '/sensor/lidar/scan', self.lidar_callback, qos_sensor
        )
        self.face_detections_sub = self.create_subscription(
            FaceDetections if CUSTOM_MSGS_AVAILABLE else String,
            '/face_detection/detections',
            self.face_detections_callback,
            qos_sensor,
        )
        self.nav_goal_sub = self.create_subscription(
            PoseStamped, '/navigation/goal', self.nav_goal_callback, 10
        )

        # Service для изменения режима (можно добавить позже)
        # self.mode_service = self.create_service(SetMode, '/controller/set_mode', self.set_mode_callback)

        # Timer for state updates
        self.create_timer(1.0 / update_rate, self.update_loop)
        self.create_timer(1.0, self.status_update_loop)  # Статус раз в секунду

        self.get_logger().info(f'Controller node started in {self.state_machine.get_mode().value} mode')

    def _on_mode_change(self, from_mode: RobotMode, to_mode: RobotMode):
        """Callback при изменении режима.

        Args:
            from_mode: Предыдущий режим
            to_mode: Новый режим
        """
        self.get_logger().info(
            f'Mode changed: {from_mode.value} -> {to_mode.value}'
        )

        # Останавливаем движение при переходе в режим ошибки или аварийной остановки
        if to_mode in [RobotMode.ERROR, RobotMode.EMERGENCY_STOP]:
            self._emergency_stop()

    def lidar_callback(self, msg: LaserScan):
        """Callback для данных лидара.

        Args:
            msg: Сообщение LaserScan
        """
        self.last_lidar_scan = msg
        self.subsystem_status['lidar'] = True

        # Проверка на препятствия для аварийной остановки
        if self.state_machine.get_mode() not in [RobotMode.EMERGENCY_STOP, RobotMode.ERROR]:
            min_distance = min(msg.ranges) if msg.ranges else float('inf')
            if min_distance < self.emergency_stop_distance:
                self.get_logger().warn(
                    f'Препятствие слишком близко: {min_distance:.2f}m, аварийная остановка!'
                )
                self.state_machine.transition_to(RobotMode.EMERGENCY_STOP)

    def face_detections_callback(self, msg):
        """Callback для обнаруженных лиц.

        Args:
            msg: Сообщение FaceDetections или String
        """
        self.last_face_detections = msg
        self.subsystem_status['face_detection'] = True

        # Переход в режим отслеживания при обнаружении лиц в режиме IDLE
        if (
            self.state_machine.get_mode() == RobotMode.IDLE
            and CUSTOM_MSGS_AVAILABLE
            and hasattr(msg, 'count')
            and msg.count > 0
        ):
            if self.state_machine.can_transition_to(RobotMode.TRACKING):
                self.state_machine.transition_to(RobotMode.TRACKING)

    def nav_goal_callback(self, msg: PoseStamped):
        """Callback для цели навигации.

        Args:
            msg: Целевая позиция
        """
        if self.state_machine.can_transition_to(RobotMode.NAVIGATION):
            self.state_machine.transition_to(RobotMode.NAVIGATION)
            self.get_logger().info(f'Received navigation goal: {msg.pose.position}')

    def update_loop(self):
        """Main update loop."""
        current_mode = self.state_machine.get_mode()

        if current_mode == RobotMode.IDLE:
            self._handle_idle_mode()
        elif current_mode == RobotMode.NAVIGATION:
            self._handle_navigation_mode()
        elif current_mode == RobotMode.TRACKING:
            self._handle_tracking_mode()
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

        # Можно добавить логику медленного поворота камеры для поиска людей

    def _handle_navigation_mode(self):
        """Обработка режима навигации."""
        # Навигация обрабатывается узлом navigation_node
        # Контроллер только отслеживает статус
        pass

    def _handle_tracking_mode(self):
        """Обработка режима отслеживания."""
        # Отслеживание обрабатывается соответствующими узлами
        # Контроллер координирует их работу
        pass

    def _handle_error_mode(self):
        """Обработка режима ошибки."""
        self._stop_movement()

        # Попытка восстановления после таймаута
        # Можно добавить логику автоматического восстановления

    def _handle_emergency_stop_mode(self):
        """Обработка режима аварийной остановки."""
        self._emergency_stop()

        # После проверки препятствий можно перейти в IDLE
        if (
            self.last_lidar_scan
            and min(self.last_lidar_scan.ranges) > self.emergency_stop_distance * 1.5
        ):
            if self.state_machine.can_transition_to(RobotMode.IDLE):
                self.state_machine.transition_to(RobotMode.IDLE)

    def _stop_movement(self):
        """Останавливает движение робота."""
        cmd = Twist()
        self.cmd_vel_pub.publish(cmd)

    def _emergency_stop(self):
        """Аварийная остановка."""
        self._stop_movement()
        self.get_logger().error('EMERGENCY STOP ACTIVATED!')

    def _publish_state(self):
        """Публикует состояние контроллера."""
        if CUSTOM_MSGS_AVAILABLE:
            state = ControllerState()
            state.header = Header()
            state.header.stamp = self.get_clock().now().to_msg()
            state.header.frame_id = 'base_link'
            state.mode = self.state_machine.get_mode().value
            state.lidar_active = self.subsystem_status['lidar']
            state.camera_active = self.subsystem_status['camera']
            state.face_detection_active = self.subsystem_status['face_detection']
            state.speech_active = self.subsystem_status['speech']
            state.navigation_active = self.subsystem_status['navigation']
            state.stm32_connected = self.subsystem_status['stm32']
            state.battery_level = self.battery_level
            state.uptime = time.time() - self.start_time
            state.status_message = f'Running in {self.state_machine.get_mode().value} mode'
            self.state_pub.publish(state)
        else:
            # Fallback на String
            msg = String()
            msg.data = f'Mode: {self.state_machine.get_mode().value}'
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
            status.header.frame_id = 'base_link'

            # Определяем системный статус
            if self.state_machine.get_mode() == RobotMode.EMERGENCY_STOP:
                status.system_status = 'emergency_stop'
            elif self.state_machine.get_mode() == RobotMode.ERROR:
                status.system_status = 'error'
            elif any(not active for active in self.subsystem_status.values()):
                status.system_status = 'warning'
            else:
                status.system_status = 'operational'

            # TODO: Получить реальные метрики системы
            status.cpu_temperature = 0.0
            status.memory_usage = 0
            status.cpu_usage = 0

            # Используем состояние контроллера
            if hasattr(self, 'state_pub'):
                # Можно создать ControllerState здесь
                pass

            status.error_message = ''
            self.status_pub.publish(status)


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


if __name__ == '__main__':
    main()
