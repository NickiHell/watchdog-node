"""ROS2 узел навигации с построением карты на основе лидара."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist, PoseStamped, PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Path, Odometry
from std_msgs.msg import String
from typing import Optional, List
import math
import time

from watchdog_navigation.obstacle_avoidance import ObstacleAvoidance
from watchdog_navigation.slam_mapper import SLAMMapper
from watchdog_navigation.path_planner import PathPlanner


class NavigationNode(Node):
    """ROS2 узел для навигации с построением карты."""

    def __init__(self):
        super().__init__('navigation_node')

        # Параметры
        self.declare_parameter('safety_distance', 0.3)
        self.declare_parameter('max_linear_velocity', 0.5)
        self.declare_parameter('max_angular_velocity', 1.0)
        self.declare_parameter('goal_tolerance', 0.1)
        self.declare_parameter('use_slam', True)  # Использовать SLAM для карты
        self.declare_parameter('inflation_radius', 0.3)

        # Инициализация модулей
        safety_distance = self.get_parameter('safety_distance').get_parameter_value().double_value
        max_linear = self.get_parameter('max_linear_velocity').get_parameter_value().double_value
        max_angular = self.get_parameter('max_angular_velocity').get_parameter_value().double_value

        self.obstacle_avoidance = ObstacleAvoidance(
            safety_distance=safety_distance,
            max_linear_velocity=max_linear,
            max_angular_velocity=max_angular
        )

        self.use_slam = self.get_parameter('use_slam').get_parameter_value().bool_value
        if self.use_slam:
            self.slam_mapper = SLAMMapper(self)
        else:
            self.slam_mapper = None

        inflation_radius = self.get_parameter('inflation_radius').get_parameter_value().double_value
        self.path_planner = PathPlanner(inflation_radius=inflation_radius)

        # Состояние
        self.current_goal: Optional[PoseStamped] = None
        self.current_path: List[tuple] = []
        self.current_path_index = 0
        self.navigation_mode = 'idle'  # idle, exploring, navigating
        self.goal_tolerance = self.get_parameter('goal_tolerance').get_parameter_value().double_value
        self.current_odom: Optional[Odometry] = None
        self.current_robot_yaw = 0.0  # Текущий угол робота (из odometry)

        # Издатели
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status_pub = self.create_publisher(String, '/navigation/status', 10)

        # Подписчики
        self.lidar_sub = self.create_subscription(
            LaserScan,
            '/sensor/lidar/scan',
            self.lidar_callback,
            10
        )

        self.goal_sub = self.create_subscription(
            PoseStamped,
            '/navigation/goal',
            self.goal_callback,
            10
        )

        self.cancel_sub = self.create_subscription(
            String,
            '/navigation/cancel',
            self.cancel_callback,
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # Таймеры
        self.create_timer(0.1, self.navigation_loop)  # 10 Hz
        self.create_timer(1.0, self.status_timer)

        self.get_logger().info('Navigation node запущен')
        if self.use_slam:
            self.get_logger().info('SLAM включен - карта будет строиться автоматически')

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

        if self.use_slam and self.slam_mapper:
            # Планируем путь на карте
            robot_pos = self.slam_mapper.get_robot_position()
            if robot_pos:
                goal_pos = (msg.pose.position.x, msg.pose.position.y)
                map_data = self.slam_mapper.get_map_data_as_array()

                if map_data is not None and self.slam_mapper.map:
                    map_info = {
                        'origin_x': self.slam_mapper.map.info.origin.position.x,
                        'origin_y': self.slam_mapper.map.info.origin.position.y,
                        'resolution': self.slam_mapper.map.info.resolution
                    }

                    path = self.path_planner.plan_path(robot_pos, goal_pos, map_data, map_info)
                    if path:
                        self.current_path = self.path_planner.simplify_path(path)
                        self.navigation_mode = 'navigating'
                        self.get_logger().info(f'Путь запланирован: {len(self.current_path)} точек')
                    else:
                        self.get_logger().warn('Не удалось найти путь к цели')
                        self.current_goal = None
                else:
                    self.get_logger().warn('Карта еще не построена')
            else:
                self.get_logger().warn('Позиция робота неизвестна')
        else:
            # Простой режим - движение напрямую к цели
            self.navigation_mode = 'navigating'
            self.get_logger().info('Начато движение к цели (простой режим)')

    def odom_callback(self, msg: Odometry):
        """Обработчик обновления одометрии.

        Args:
            msg: Сообщение Odometry
        """
        self.current_odom = msg
        
        # Извлекаем угол из quaternion
        q = msg.pose.pose.orientation
        # Простой расчет yaw из quaternion
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_robot_yaw = math.atan2(siny_cosp, cosy_cosp)

    def cancel_callback(self, msg: String):
        """Обработчик отмены навигации."""
        self.current_goal = None
        self.current_path = []
        self.navigation_mode = 'idle'
        self.get_logger().info('Навигация отменена')

        # Останавливаем робота
        cmd_vel = Twist()
        self.cmd_vel_pub.publish(cmd_vel)

    def navigation_loop(self):
        """Основной цикл навигации."""
        if self.navigation_mode == 'idle':
            return

        # Проверяем наличие цели
        if self.current_goal is None:
            self.navigation_mode = 'idle'
            return

        # Получаем текущую позицию
        if self.use_slam and self.slam_mapper and self.slam_mapper.is_ready():
            robot_pos = self.slam_mapper.get_robot_position()
        elif self.current_odom:
            # Используем odometry
            pos = self.current_odom.pose.pose.position
            robot_pos = (pos.x, pos.y)
        else:
            self.get_logger().warn('Позиция робота неизвестна')
            return

        # Вычисляем команду движения
        cmd_vel = Twist()

        if self.current_path and self.use_slam:
            # Двигаемся по пути
            if self.current_path_index < len(self.current_path):
                target = self.current_path[self.current_path_index]
                cmd_vel = self._compute_path_command(robot_pos, target)
            else:
                # Достигли конца пути - идем к финальной цели
                goal_pos = (self.current_goal.pose.position.x, self.current_goal.pose.position.y)
                cmd_vel = self._compute_path_command(robot_pos, goal_pos)

                # Проверяем, достигли ли цели
                distance = math.sqrt(
                    (robot_pos[0] - goal_pos[0]) ** 2 +
                    (robot_pos[1] - goal_pos[1]) ** 2
                )
                if distance < self.goal_tolerance:
                    self.get_logger().info('Цель достигнута!')
                    self.current_goal = None
                    self.current_path = []
                    self.navigation_mode = 'idle'
                    cmd_vel = Twist()
        else:
            # Простой режим - движение напрямую к цели
            goal_pos = (self.current_goal.pose.position.x, self.current_goal.pose.position.y)
            cmd_vel = self._compute_path_command(robot_pos, goal_pos)

            # Проверяем достижение цели
            distance = math.sqrt(
                (robot_pos[0] - goal_pos[0]) ** 2 +
                (robot_pos[1] - goal_pos[1]) ** 2
            )
            if distance < self.goal_tolerance:
                self.get_logger().info('Цель достигнута!')
                self.current_goal = None
                self.navigation_mode = 'idle'
                cmd_vel = Twist()

        # Применяем избежание препятствий
        safe_linear, safe_angular = self.obstacle_avoidance.compute_safe_velocity(
            cmd_vel.linear.x, cmd_vel.angular.z
        )

        cmd_vel.linear.x = safe_linear
        cmd_vel.angular.z = safe_angular

        # Публикуем команду
        self.cmd_vel_pub.publish(cmd_vel)

    def _compute_path_command(self, robot_pos: tuple, target_pos: tuple) -> Twist:
        """Вычисляет команду движения к целевой точке.

        Args:
            robot_pos: Позиция робота (x, y)
            target_pos: Целевая позиция (x, y)

        Returns:
            Команда движения Twist
        """
        cmd_vel = Twist()

        # Вычисляем расстояние и угол до цели
        dx = target_pos[0] - robot_pos[0]
        dy = target_pos[1] - robot_pos[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < self.goal_tolerance:
            return cmd_vel  # Останавливаемся

        # Вычисляем желаемый угол
        desired_angle = math.atan2(dy, dx)

        # Получаем текущий угол робота из odometry
        current_angle = self.current_robot_yaw

        # Вычисляем разницу углов
        angle_diff = desired_angle - current_angle
        # Нормализуем в [-pi, pi]
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Вычисляем скорости
        max_linear = self.get_parameter('max_linear_velocity').get_parameter_value().double_value
        max_angular = self.get_parameter('max_angular_velocity').get_parameter_value().double_value

        # Если далеко от цели, сначала выравниваем направление
        if abs(angle_diff) > 0.2:  # ~11 градусов
            cmd_vel.angular.z = max_angular * (angle_diff / abs(angle_diff)) * min(abs(angle_diff), 1.0)
        else:
            # Двигаемся вперед
            cmd_vel.linear.x = max_linear * min(distance, 1.0)
            cmd_vel.angular.z = max_angular * angle_diff  # Небольшая коррекция направления

        return cmd_vel

    def status_timer(self):
        """Таймер для публикации статуса."""
        status = {
            'mode': self.navigation_mode,
            'has_goal': self.current_goal is not None,
            'path_length': len(self.current_path),
            'slam_ready': self.slam_mapper.is_ready() if self.slam_mapper else False
        }

        status_str = f"mode:{status['mode']},goal:{status['has_goal']},path:{status['path_length']},slam:{status['slam_ready']}"
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


if __name__ == '__main__':
    main()

