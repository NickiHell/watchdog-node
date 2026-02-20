"""ROS2 узел навигации для дрона с поддержкой 3D навигации."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist, PoseStamped
from std_msgs.msg import String

from watchdog_navigation.obstacle_avoidance import ObstacleAvoidance
from watchdog_navigation.slam_mapper import SLAMMapper
from watchdog_navigation.path_planner import PathPlanner
from watchdog_navigation.local_navigator import LocalNavigator
from watchdog_navigation.flight_actions import FlightActions


class NavigationNode(Node):
    """ROS2 узел для навигации с построением карты."""

    def __init__(self):
        super().__init__("navigation_node")

        # Параметры
        self.declare_parameter("safety_distance", 1.0)
        self.declare_parameter("max_linear_velocity", 5.0)
        self.declare_parameter("max_vertical_velocity", 2.0)
        self.declare_parameter("max_angular_velocity", 1.5)
        self.declare_parameter("goal_tolerance", 0.5)
        self.declare_parameter("use_slam", False)  # На высотах >30м SLAM не нужен
        self.declare_parameter("inflation_radius", 1.0)
        self.declare_parameter("default_height", 30.0)
        self.declare_parameter("max_height", 200.0)  # Ограничение эшелона

        # Инициализация модулей
        safety_distance = self.get_parameter("safety_distance").get_parameter_value().double_value
        max_linear = self.get_parameter("max_linear_velocity").get_parameter_value().double_value
        max_angular = self.get_parameter("max_angular_velocity").get_parameter_value().double_value

        self.obstacle_avoidance = ObstacleAvoidance(
            safety_distance=safety_distance,
            max_linear_velocity=max_linear,
            max_angular_velocity=max_angular,
        )

        self.local_navigator = LocalNavigator()
        self.flight_actions = FlightActions()

        self.use_slam = self.get_parameter("use_slam").get_parameter_value().bool_value
        if self.use_slam:
            self.slam_mapper = SLAMMapper(self)
        else:
            self.slam_mapper = None

        inflation_radius = self.get_parameter("inflation_radius").get_parameter_value().double_value
        self.path_planner = PathPlanner(inflation_radius=inflation_radius)

        # Состояние
        self.current_goal: PoseStamped | None = None
        self.current_path: list[tuple] = []
        self.current_path_index = 0
        self.navigation_mode = "idle"  # idle, exploring, navigating
        self.goal_tolerance = self.get_parameter("goal_tolerance").get_parameter_value().double_value
        self.current_local_position: PoseStamped | None = None

        # Издатели
        self.cmd_vel_pub = self.create_publisher(Twist, "/cmd_vel", 10)
        self.status_pub = self.create_publisher(String, "/navigation/status", 10)

        # Подписчики
        self.lidar_sub = self.create_subscription(LaserScan, "/sensor/lidar/scan", self.lidar_callback, 10)
        self.goal_sub = self.create_subscription(PoseStamped, "/navigation/goal", self.goal_callback, 10)

        self.cancel_sub = self.create_subscription(String, "/navigation/cancel", self.cancel_callback, 10)

        self.local_pos_sub = self.create_subscription(
            PoseStamped, "/mavros/local_position/pose", self.local_position_callback, 10
        )

        # Таймеры
        self.create_timer(0.1, self.navigation_loop)  # 10 Hz
        self.create_timer(1.0, self.status_timer)

        self.max_height = self.get_parameter("max_height").value

        self.get_logger().info(
            f"Navigation node запущен | max_height={self.max_height}м "
            f"| max_vel={max_linear}м/с | SLAM={'вкл' if self.use_slam else 'выкл'}"
        )

    def lidar_callback(self, msg: LaserScan):
        """Обработчик данных лидара.

        Args:
            msg: Сообщение LaserScan
        """
        self.obstacle_avoidance.update_scan(msg)

    def goal_callback(self, msg: PoseStamped):
        """Обработчик новой цели.

        Args:
            msg: Целевая позиция
        """
        self.current_goal = msg
        self.current_path_index = 0

        # Если высота не указана, используем высоту по умолчанию
        if msg.pose.position.z == 0.0:
            default_height = self.get_parameter("default_height").value
            msg.pose.position.z = default_height

        # Ограничиваем высоту целевой точки
        if msg.pose.position.z > self.max_height:
            self.get_logger().warn(f"Цель выше лимита {self.max_height}м, ограничиваем до {self.max_height}м")
            msg.pose.position.z = self.max_height

        if self.use_slam and self.slam_mapper:
            # Планируем путь на карте (3D)
            robot_pos_3d = None
            if self.current_local_position:
                pos = self.current_local_position.pose.position
                robot_pos_3d = (pos.x, pos.y, pos.z)
            elif self.slam_mapper.is_ready():
                slam_pos = self.slam_mapper.get_robot_position()
                default_height = self.get_parameter("default_height").get_parameter_value().double_value
                if len(slam_pos) == 2:
                    robot_pos_3d = (slam_pos[0], slam_pos[1], default_height)
                else:
                    robot_pos_3d = slam_pos

            if robot_pos_3d:
                goal_pos_3d = (msg.pose.position.x, msg.pose.position.y, msg.pose.position.z)
                # Планируем путь в 3D
                path = self.path_planner.plan_path(robot_pos_3d, goal_pos_3d)
                if path:
                    self.current_path = self.path_planner.simplify_path(path)
                    self.navigation_mode = "navigating"
                    self.get_logger().info(f"Путь запланирован: {len(self.current_path)} точек")
                else:
                    self.get_logger().warn("Не удалось найти путь к цели")
                    self.current_goal = None
            else:
                self.get_logger().warn("Позиция дрона неизвестна")
        else:
            # Простой режим - движение напрямую к цели
            self.navigation_mode = "navigating"
            self.get_logger().info(
                f"Начато движение к цели: ({msg.pose.position.x:.2f}, {msg.pose.position.y:.2f}, {msg.pose.position.z:.2f})"
            )

    def local_position_callback(self, msg: PoseStamped):
        """Обработчик локальной позиции от Pixhawk.

        Args:
            msg: Сообщение PoseStamped с локальной позицией
        """
        self.current_local_position = msg
        self.local_navigator.update_position(msg)

    def cancel_callback(self, msg: String):
        """Обработчик отмены навигации."""
        self.current_goal = None
        self.current_path = []
        self.navigation_mode = "idle"
        self.get_logger().info("Навигация отменена")

        # Останавливаем робота
        cmd_vel = Twist()
        self.cmd_vel_pub.publish(cmd_vel)

    def navigation_loop(self):
        """Основной цикл навигации."""
        if self.navigation_mode == "idle":
            return

        # Проверяем наличие цели
        if self.current_goal is None:
            self.navigation_mode = "idle"
            return

        # Получаем текущую позицию
        if self.current_local_position:
            pass
        elif self.use_slam and self.slam_mapper and self.slam_mapper.is_ready():
            slam_pos = self.slam_mapper.get_robot_position()
            # Добавляем высоту по умолчанию если SLAM не дает высоту
            if len(slam_pos) == 2:
                default_height = self.get_parameter("default_height").get_parameter_value().double_value
                (slam_pos[0], slam_pos[1], default_height)
            else:
                pass
        else:
            self.get_logger().warn("Позиция дрона неизвестна")
            return

        # Вычисляем команду движения
        goal_pos = (
            self.current_goal.pose.position.x,
            self.current_goal.pose.position.y,
            self.current_goal.pose.position.z,
        )

        # Используем local_navigator для вычисления команды скорости
        max_vel = self.get_parameter("max_linear_velocity").get_parameter_value().double_value
        max_vert_vel = self.get_parameter("max_vertical_velocity").get_parameter_value().double_value

        cmd_vel = self.local_navigator.compute_velocity_command(
            goal_pos, max_velocity=max_vel, max_vertical_velocity=max_vert_vel
        )

        if cmd_vel is None:
            self.get_logger().warn("Не удалось вычислить команду скорости")
            return

        # Проверяем достижение цели
        if self.local_navigator.is_at_position(goal_pos, self.goal_tolerance):
            self.get_logger().info("Цель достигнута!")
            self.current_goal = None
            self.current_path = []
            self.navigation_mode = "idle"
            cmd_vel = self.flight_actions.hover()

        # Применяем избежание препятствий (только для горизонтального движения)
        safe_linear, safe_angular = self.obstacle_avoidance.compute_safe_velocity(cmd_vel.linear.x, cmd_vel.angular.z)

        cmd_vel.linear.x = safe_linear
        cmd_vel.angular.z = safe_angular
        # Вертикальная скорость не изменяется избежанием препятствий

        # Публикуем команду
        self.cmd_vel_pub.publish(cmd_vel)

    def status_timer(self):
        """Таймер для публикации статуса."""
        status = {
            "mode": self.navigation_mode,
            "has_goal": self.current_goal is not None,
            "path_length": len(self.current_path),
            "slam_ready": self.slam_mapper.is_ready() if self.slam_mapper else False,
        }

        status_str = (
            f"mode:{status['mode']},goal:{status['has_goal']},path:{status['path_length']},slam:{status['slam_ready']}"
        )
        msg = String()
        msg.data = status_str
        self.status_pub.publish(msg)


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = NavigationNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
