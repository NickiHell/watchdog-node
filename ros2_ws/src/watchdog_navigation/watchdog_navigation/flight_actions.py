"""Модуль действий полета для дрона."""

from geometry_msgs.msg import PoseStamped, Twist


class FlightActions:
    """Класс для выполнения действий полета дрона."""

    def __init__(self):
        self.current_height = 0.0
        self.is_flying = False
        self.is_landing = False

    def takeoff(self, height: float) -> PoseStamped | None:
        """Создает команду взлета на заданную высоту.

        Args:
            height: Высота взлета в метрах

        Returns:
            Команда позиции для взлета или None
        """
        if height <= 0:
            return None

        pose = PoseStamped()
        pose.pose.position.x = 0.0
        pose.pose.position.y = 0.0
        pose.pose.position.z = height
        pose.pose.orientation.w = 1.0

        self.current_height = height
        self.is_flying = True
        return pose

    def land(self) -> Twist:
        """Создает команду посадки.

        Returns:
            Команда скорости для посадки
        """
        cmd = Twist()
        cmd.linear.z = -0.5  # Скорость снижения (м/с)
        self.is_landing = True
        return cmd

    def hover(self) -> Twist:
        """Создает команду зависания на месте.

        Returns:
            Команда скорости для зависания
        """
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.linear.y = 0.0
        cmd.linear.z = 0.0
        cmd.angular.z = 0.0
        return cmd

    def goto_waypoint(self, x: float, y: float, z: float) -> PoseStamped:
        """Создает команду движения к точке маршрута.

        Args:
            x: Координата X в метрах
            y: Координата Y в метрах
            z: Высота Z в метрах

        Returns:
            Команда позиции для движения к точке
        """
        pose = PoseStamped()
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0

        self.current_height = z
        return pose

    def move_velocity(self, vx: float, vy: float, vz: float, yaw_rate: float = 0.0) -> Twist:
        """Создает команду движения с заданной скоростью.

        Args:
            vx: Скорость по X (м/с)
            vy: Скорость по Y (м/с)
            vz: Скорость по Z (м/с)
            yaw_rate: Угловая скорость поворота (рад/с)

        Returns:
            Команда скорости
        """
        cmd = Twist()
        cmd.linear.x = vx
        cmd.linear.y = vy
        cmd.linear.z = vz
        cmd.angular.z = yaw_rate
        return cmd

    def emergency_land(self) -> Twist:
        """Создает команду аварийной посадки.

        Returns:
            Команда скорости для быстрой посадки
        """
        cmd = Twist()
        cmd.linear.x = 0.0
        cmd.linear.y = 0.0
        cmd.linear.z = -1.0  # Быстрое снижение
        cmd.angular.z = 0.0
        self.is_landing = True
        return cmd
