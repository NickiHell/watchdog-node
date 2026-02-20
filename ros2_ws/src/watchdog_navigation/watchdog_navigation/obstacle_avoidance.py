"""Модуль избежания препятствий на основе данных лидара."""

import numpy as np
from sensor_msgs.msg import LaserScan
from rclpy.logging import get_logger


class ObstacleAvoidance:
    """Класс для избежания препятствий на основе лидара."""

    def __init__(
        self,
        safety_distance: float = 0.3,
        max_linear_velocity: float = 0.5,
        max_angular_velocity: float = 1.0,
        front_sector_angle: float = 1.57,  # 90 градусов по обе стороны
        min_distance_to_person: float = 1.0,  # Минимальное расстояние до людей (м)
    ):
        """Инициализирует модуль избежания препятствий.

        Args:
            safety_distance: Минимальное безопасное расстояние до препятствия (метры)
            max_linear_velocity: Максимальная линейная скорость (м/с)
            max_angular_velocity: Максимальная угловая скорость (рад/с)
            front_sector_angle: Угол переднего сектора для проверки (радианы)
            min_distance_to_person: Минимальное расстояние до людей для безопасности (метры)
        """
        self.safety_distance = safety_distance
        self.min_distance_to_person = min_distance_to_person
        self.max_linear_velocity = max_linear_velocity
        self.max_angular_velocity = max_angular_velocity
        self.front_sector_angle = front_sector_angle
        self.logger = get_logger("ObstacleAvoidance")
        self.last_scan: LaserScan | None = None
        self.person_detected = False  # Флаг обнаружения человека

    def update_scan(self, scan: LaserScan):
        """Обновляет данные скана лидара.

        Args:
            scan: Сообщение LaserScan от лидара
        """
        self.last_scan = scan

    def set_person_detected(self, detected: bool):
        """Устанавливает флаг обнаружения человека.

        Args:
            detected: True если человек обнаружен
        """
        self.person_detected = detected

    def compute_safe_velocity(self, desired_linear: float, desired_angular: float) -> tuple[float, float]:
        """Вычисляет безопасную скорость движения.

        Args:
            desired_linear: Желаемая линейная скорость
            desired_angular: Желаемая угловая скорость

        Returns:
            Кортеж (safe_linear, safe_angular) - безопасные скорости
        """
        if self.last_scan is None:
            # Если человек обнаружен, но нет данных лидара - останавливаемся
            if self.person_detected:
                return 0.0, desired_angular
            return desired_linear, desired_angular

        # Проверяем препятствия в переднем секторе
        front_obstacle = self._check_front_obstacle()

        # Если человек обнаружен, используем увеличенное безопасное расстояние
        effective_safety_distance = self.min_distance_to_person if self.person_detected else self.safety_distance

        if front_obstacle:
            # Есть препятствие впереди - останавливаемся или поворачиваем
            distance, angle = front_obstacle

            if distance < effective_safety_distance:
                # Слишком близко - останавливаемся и поворачиваем
                if self.person_detected:
                    self.logger.warning(
                        f"Человек слишком близко: {distance:.2f}m, "
                        f"требуется минимум {self.min_distance_to_person:.2f}m!"
                    )
                safe_linear = 0.0
                safe_angular = self._compute_avoidance_angle(angle)
            else:
                # Замедляемся пропорционально расстоянию
                if distance < effective_safety_distance * 1.5:
                    # В зоне замедления
                    safe_linear = desired_linear * (
                        (distance - effective_safety_distance) / (effective_safety_distance * 0.5)
                    )
                    safe_linear = max(0.0, min(safe_linear, self.max_linear_velocity))
                else:
                    # Достаточно далеко
                    safe_linear = desired_linear
                    safe_linear = min(safe_linear, self.max_linear_velocity)
                safe_angular = desired_angular
        else:
            # Нет препятствий - можем двигаться
            # Но если человек обнаружен, ограничиваем скорость приближения
            if self.person_detected and desired_linear > 0:
                # Ограничиваем скорость приближения к человеку
                safe_linear = min(desired_linear, self.max_linear_velocity * 0.5)
            else:
                safe_linear = np.clip(desired_linear, -self.max_linear_velocity, self.max_linear_velocity)
            safe_angular = np.clip(desired_angular, -self.max_angular_velocity, self.max_angular_velocity)

        return safe_linear, safe_angular

    def _check_front_obstacle(self) -> tuple[float, float] | None:
        """Проверяет наличие препятствий в переднем секторе.

        Returns:
            Кортеж (distance, angle) ближайшего препятствия или None
        """
        if self.last_scan is None or len(self.last_scan.ranges) == 0:
            return None

        ranges = np.array(self.last_scan.ranges)
        angles = np.linspace(self.last_scan.angle_min, self.last_scan.angle_max, len(ranges))

        # Фильтруем валидные данные
        valid_mask = (ranges >= self.last_scan.range_min) & (ranges <= self.last_scan.range_max) & (np.isfinite(ranges))

        if not np.any(valid_mask):
            return None

        valid_ranges = ranges[valid_mask]
        valid_angles = angles[valid_mask]

        # Проверяем передний сектор (от -front_sector_angle/2 до +front_sector_angle/2)
        front_mask = np.abs(valid_angles) < (self.front_sector_angle / 2.0)
        front_ranges = valid_ranges[front_mask]
        front_angles = valid_angles[front_mask]

        if len(front_ranges) == 0:
            return None

        # Находим ближайшее препятствие
        min_idx = np.argmin(front_ranges)
        min_distance = front_ranges[min_idx]
        min_angle = front_angles[min_idx]

        return (float(min_distance), float(min_angle))

    def _compute_avoidance_angle(self, obstacle_angle: float) -> float:
        """Вычисляет угол поворота для объезда препятствия.

        Args:
            obstacle_angle: Угол до препятствия

        Returns:
            Угловая скорость для поворота (рад/с)
        """
        # Поворачиваем в сторону, противоположную препятствию
        # Если препятствие справа (угол > 0), поворачиваем влево (отрицательная скорость)
        # Если препятствие слева (угол < 0), поворачиваем вправо (положительная скорость)

        # Нормализуем угол в диапазон [-pi, pi]
        if obstacle_angle > np.pi:
            obstacle_angle -= 2 * np.pi
        elif obstacle_angle < -np.pi:
            obstacle_angle += 2 * np.pi

        # Вычисляем направление поворота
        if obstacle_angle > 0:
            # Препятствие справа - поворачиваем влево
            angular_velocity = -self.max_angular_velocity
        else:
            # Препятствие слева - поворачиваем вправо
            angular_velocity = self.max_angular_velocity

        return angular_velocity

    def check_clear_path(self, direction_angle: float = 0.0, width: float = 0.3) -> bool:
        """Проверяет, свободен ли путь в заданном направлении.

        Args:
            direction_angle: Угол направления (радианы, 0 = прямо)
            width: Ширина проверяемого пути (радианы)

        Returns:
            True если путь свободен
        """
        if self.last_scan is None:
            return False

        ranges = np.array(self.last_scan.ranges)
        angles = np.linspace(self.last_scan.angle_min, self.last_scan.angle_max, len(ranges))

        # Фильтруем валидные данные
        valid_mask = (ranges >= self.last_scan.range_min) & (ranges <= self.last_scan.range_max) & (np.isfinite(ranges))

        if not np.any(valid_mask):
            return True  # Нет данных - считаем путь свободным

        valid_ranges = ranges[valid_mask]
        valid_angles = angles[valid_mask]

        # Проверяем сектор в заданном направлении
        sector_mask = (valid_angles >= direction_angle - width / 2.0) & (valid_angles <= direction_angle + width / 2.0)

        if not np.any(sector_mask):
            return True  # Нет данных в этом секторе

        sector_ranges = valid_ranges[sector_mask]

        # Проверяем, есть ли препятствия ближе безопасного расстояния
        min_distance = np.min(sector_ranges)
        return min_distance >= self.safety_distance

    def get_safe_direction(self) -> float | None:
        """Возвращает направление свободного пути.

        Returns:
            Угол свободного направления или None
        """
        if self.last_scan is None:
            return None

        ranges = np.array(self.last_scan.ranges)
        angles = np.linspace(self.last_scan.angle_min, self.last_scan.angle_max, len(ranges))

        # Фильтруем валидные данные
        valid_mask = (ranges >= self.last_scan.range_min) & (ranges <= self.last_scan.range_max) & (np.isfinite(ranges))

        if not np.any(valid_mask):
            return 0.0  # Нет данных - двигаемся прямо

        valid_ranges = ranges[valid_mask]
        valid_angles = angles[valid_mask]

        # Разбиваем на секторы и ищем наиболее свободный
        sector_count = 8
        sector_size = 2 * np.pi / sector_count
        best_sector = 0
        best_distance = 0.0

        for i in range(sector_count):
            sector_start = -np.pi + i * sector_size
            sector_end = -np.pi + (i + 1) * sector_size

            sector_mask = (valid_angles >= sector_start) & (valid_angles < sector_end)

            if np.any(sector_mask):
                sector_ranges = valid_ranges[sector_mask]
                avg_distance = np.mean(sector_ranges)
                min_distance = np.min(sector_ranges)

                # Оцениваем качество сектора (учитываем среднее и минимум)
                score = avg_distance * 0.7 + min_distance * 0.3

                if score > best_distance and min_distance >= self.safety_distance:
                    best_distance = score
                    best_sector = i

        # Возвращаем центр лучшего сектора
        best_angle = -np.pi + (best_sector + 0.5) * sector_size
        return float(best_angle)
