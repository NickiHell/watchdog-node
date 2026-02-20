"""ROS2 узел для связи с Pixhawk через mavros.

Этот узел:
- Подписывается на команды движения и публикует их в mavros
- Читает телеметрию от Pixhawk через mavros
- Управляет режимами полета PX4
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, PoseStamped
from mavros_msgs.msg import State, BatteryStatus, RCIn
from mavros_msgs.srv import SetMode, CommandBool
from std_msgs.msg import String


class PixhawkInterfaceNode(Node):
    """ROS2 узел для интерфейса с Pixhawk через mavros."""

    def __init__(self):
        super().__init__("pixhawk_interface_node")

        # Параметры
        self.declare_parameter("offboard_timeout", 5.0)  # Таймаут для OFFBOARD режима
        self.declare_parameter("arm_timeout", 10.0)  # Таймаут для арминга

        # Состояние
        self.current_state = State()
        self.current_position = PoseStamped()
        self.current_battery = BatteryStatus()
        self.offboard_setpoint_counter = 0
        self.armed = False
        self.offboard_mode = False
        self.rc_active = False
        self.rc_override = False  # RC имеет приоритет над автономными командами

        # Издатели
        self.local_pos_pub = self.create_publisher(PoseStamped, "/mavros/setpoint_position/local", 10)
        self.vel_pub = self.create_publisher(Twist, "/mavros/setpoint_velocity/cmd_vel_unstamped", 10)
        self.status_pub = self.create_publisher(String, "/pixhawk/status", 10)

        # Подписчики
        self.state_sub = self.create_subscription(State, "/mavros/state", self.state_callback, 10)

        self.local_pos_sub = self.create_subscription(
            PoseStamped, "/mavros/local_position/pose", self.local_position_callback, 10
        )

        self.battery_sub = self.create_subscription(BatteryStatus, "/mavros/battery", self.battery_callback, 10)

        self.cmd_vel_sub = self.create_subscription(Twist, "/cmd_vel", self.cmd_vel_callback, 10)

        # Подписка на RC команды (приоритет над автономными командами)
        self.rc_cmd_sub = self.create_subscription(Twist, "/rc/cmd_vel", self.rc_cmd_callback, 10)

        self.rc_in_sub = self.create_subscription(RCIn, "/mavros/rc/in", self.rc_in_callback, 10)

        # Клиенты сервисов
        self.arming_client = self.create_client(CommandBool, "/mavros/cmd/arming")
        self.set_mode_client = self.create_client(SetMode, "/mavros/set_mode")

        # Таймеры
        self.create_timer(0.1, self.offboard_timer_callback)  # 10 Hz
        self.create_timer(1.0, self.status_timer_callback)  # 1 Hz

        self.get_logger().info("Pixhawk interface node запущен")

    def state_callback(self, msg: State):
        """Обработчик состояния Pixhawk."""
        self.current_state = msg
        self.armed = msg.armed
        self.offboard_mode = msg.mode == "OFFBOARD"

    def local_position_callback(self, msg: PoseStamped):
        """Обработчик локальной позиции."""
        self.current_position = msg

    def battery_callback(self, msg: BatteryStatus):
        """Обработчик состояния батареи."""
        self.current_battery = msg

    def cmd_vel_callback(self, msg: Twist):
        """Обработчик команд движения.

        Args:
            msg: Команда скорости (geometry_msgs/Twist)
        """
        # Публикуем команду только если RC не активен
        if not self.rc_override:
            self.vel_pub.publish(msg)

    def rc_cmd_callback(self, msg: Twist):
        """Обработчик команд от RC пульта.

        Args:
            msg: Команда скорости от RC пульта
        """
        # RC команды имеют приоритет - публикуем напрямую
        self.vel_pub.publish(msg)
        self.rc_override = True

    def rc_in_callback(self, msg: RCIn):
        """Обработчик данных от RC receiver.

        Args:
            msg: Данные от RC receiver
        """
        # Проверяем, активен ли RC сигнал
        if len(msg.channels) >= 4:
            # Проверяем, что каналы в разумных пределах
            if all(1000 <= ch <= 2000 for ch in msg.channels[:4]):
                self.rc_active = True
                # Если RC активен, переключаемся в режим MANUAL или STABILIZED
                if self.current_state.mode != "MANUAL" and self.current_state.mode != "STABILIZED":
                    # Можно автоматически переключаться в MANUAL режим при активном RC
                    pass
            else:
                self.rc_active = False
                self.rc_override = False

    def set_offboard_mode(self):
        """Установка режима OFFBOARD."""
        if self.current_state.mode != "OFFBOARD":
            req = SetMode.Request()
            req.custom_mode = "OFFBOARD"
            self.set_mode_client.call_async(req)
            # В реальной реализации нужно дождаться результата
            self.get_logger().info("Запрос режима OFFBOARD")

    def arm_drone(self):
        """Арминг дрона."""
        if not self.current_state.armed:
            req = CommandBool.Request()
            req.value = True
            self.arming_client.call_async(req)
            self.get_logger().info("Запрос арминга дрона")

    def offboard_timer_callback(self):
        """Таймер для поддержания OFFBOARD режима."""
        # Отправляем setpoint для поддержания OFFBOARD режима
        if self.offboard_setpoint_counter < 10:
            # Отправляем нулевую позицию для инициализации
            pose = PoseStamped()
            pose.pose.position.x = 0.0
            pose.pose.position.y = 0.0
            pose.pose.position.z = 0.0
            self.local_pos_pub.publish(pose)
            self.offboard_setpoint_counter += 1
        else:
            # После инициализации можно переключаться в OFFBOARD
            if not self.offboard_mode:
                self.set_offboard_mode()
            if not self.armed:
                self.arm_drone()

    def status_timer_callback(self):
        """Таймер для публикации статуса."""
        status_str = (
            f"armed:{self.armed},mode:{self.current_state.mode},"
            f"battery:{self.current_battery.percentage:.1f}%,"
            f"connected:{self.current_state.connected}"
        )
        msg = String()
        msg.data = status_str
        self.status_pub.publish(msg)


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = PixhawkInterfaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
