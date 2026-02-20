"""Модуль локальной навигации для дрона."""

from geometry_msgs.msg import PoseStamped, Twist
import math


class LocalNavigator:
    """Класс для локальной навигации в системе координат Pixhawk."""

    def __init__(self):
        self.current_position: PoseStamped | None = None
        self.current_yaw = 0.0

    def update_position(self, pose: PoseStamped):
        """Обновляет текущую позицию дрона.

        Args:
            pose: Текущая позиция от Pixhawk
        """
        self.current_position = pose

        # Извлекаем yaw из quaternion
        q = pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        self.current_yaw = math.atan2(siny_cosp, cosy_cosp)

    def compute_velocity_command(
        self, target: tuple[float, float, float], max_velocity: float = 1.0, max_vertical_velocity: float = 0.5
    ) -> Twist | None:
        """Вычисляет команду скорости для движения к цели.

        Args:
            target: Целевая позиция (x, y, z)
            max_velocity: Максимальная горизонтальная скорость (м/с)
            max_vertical_velocity: Максимальная вертикальная скорость (м/с)

        Returns:
            Команда скорости или None если позиция неизвестна
        """
        if self.current_position is None:
            return None

        current = self.current_position.pose.position

        # Вычисляем разницу
        dx = target[0] - current.x
        dy = target[1] - current.y
        dz = target[2] - current.z

        distance_xy = math.sqrt(dx * dx + dy * dy)
        distance_z = abs(dz)

        # Вычисляем скорости
        cmd = Twist()

        if distance_xy > 0.1:
            # Горизонтальное движение
            desired_angle = math.atan2(dy, dx)
            angle_diff = desired_angle - self.current_yaw

            # Нормализуем угол
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            # Если угол большой, сначала поворачиваемся
            if abs(angle_diff) > 0.2:
                cmd.angular.z = max(-1.0, min(1.0, angle_diff * 2.0))
            else:
                # Двигаемся к цели
                cmd.linear.x = max_velocity * min(1.0, distance_xy)
                cmd.linear.y = 0.0
                cmd.angular.z = angle_diff * 0.5  # Небольшая коррекция

        if distance_z > 0.1:
            # Вертикальное движение
            if dz > 0:
                cmd.linear.z = max_vertical_velocity
            else:
                cmd.linear.z = -max_vertical_velocity

        return cmd

    def is_at_position(self, target: tuple[float, float, float], tolerance: float = 0.2) -> bool:
        """Проверяет, достиг ли дрон целевой позиции.

        Args:
            target: Целевая позиция (x, y, z)
            tolerance: Допустимое отклонение (м)

        Returns:
            True если дрон достиг цели
        """
        if self.current_position is None:
            return False

        current = self.current_position.pose.position

        dx = target[0] - current.x
        dy = target[1] - current.y
        dz = target[2] - current.z

        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        return distance < tolerance

    def get_current_position(self) -> tuple[float, float, float] | None:
        """Возвращает текущую позицию дрона.

        Returns:
            Текущая позиция (x, y, z) или None
        """
        if self.current_position is None:
            return None

        pos = self.current_position.pose.position
        return (pos.x, pos.y, pos.z)
