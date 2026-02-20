"""Модуль сопровождения цели для дрона."""

import cv2
import numpy as np
from typing import Optional, Tuple, Dict
from geometry_msgs.msg import Point
import math


class TargetTracker:
    """Класс для сопровождения цели (лица или объекта) на изображении."""

    def __init__(self, tracker_type: str = "CSRT"):
        """Инициализация трекера.

        Args:
            tracker_type: Тип трекера ("CSRT", "KCF", "MOSSE")
        """
        self.tracker_type = tracker_type
        self.tracker = None
        self.is_tracking = False
        self.current_bbox: Optional[Tuple[int, int, int, int]] = None
        self.tracked_target_id: Optional[str] = None

        # Параметры для управления дроном
        self.image_center_x = 0
        self.image_center_y = 0
        self.fov_horizontal = 1.0  # Горизонтальное поле зрения (радианы)
        self.fov_vertical = 1.0   # Вертикальное поле зрения (радианы)

    def init_tracker(self, frame: np.ndarray, bbox: Tuple[int, int, int, int], target_id: str = None):
        """Инициализирует трекер с начальным bounding box.

        Args:
            frame: Кадр изображения
            bbox: Bounding box (x, y, width, height)
            target_id: ID цели для отслеживания
        """
        if self.tracker_type == "CSRT":
            self.tracker = cv2.TrackerCSRT_create()
        elif self.tracker_type == "KCF":
            self.tracker = cv2.TrackerKCF_create()
        elif self.tracker_type == "MOSSE":
            self.tracker = cv2.TrackerMOSSE_create()
        else:
            self.tracker = cv2.TrackerCSRT_create()  # По умолчанию

        # Инициализируем трекер
        success = self.tracker.init(frame, bbox)

        if success:
            self.is_tracking = True
            self.current_bbox = bbox
            self.tracked_target_id = target_id
            self.image_center_x = frame.shape[1] // 2
            self.image_center_y = frame.shape[0] // 2
            return True
        else:
            self.is_tracking = False
            return False

    def update(self, frame: np.ndarray) -> Tuple[bool, Optional[Tuple[int, int, int, int]]]:
        """Обновляет позицию цели на новом кадре.

        Args:
            frame: Новый кадр изображения

        Returns:
            Кортеж (success, bbox) - успех отслеживания и новый bounding box
        """
        if not self.is_tracking or self.tracker is None:
            return False, None

        success, bbox = self.tracker.update(frame)

        if success:
            self.current_bbox = bbox
            return True, bbox
        else:
            self.is_tracking = False
            self.current_bbox = None
            return False, None

    def compute_tracking_command(self, frame_width: int, frame_height: int) -> Optional[Dict[str, float]]:
        """Вычисляет команду для удержания цели в центре кадра и следования за ней.

        Дрон должен:
        - Держать расстояние ~5 метров от цели
        - Следовать за целью, если она уходит в сторону
        - Удерживать цель в центре кадра по вертикали

        Args:
            frame_width: Ширина кадра
            frame_height: Высота кадра

        Returns:
            Словарь с командами движения или None
        """
        if not self.is_tracking or self.current_bbox is None:
            return None

        x, y, w, h = self.current_bbox

        # Центр цели
        target_center_x = x + w // 2
        target_center_y = y + h // 2

        # Центр кадра
        image_center_x = frame_width // 2
        image_center_y = frame_height // 2

        # Вычисляем смещение
        dx = target_center_x - image_center_x
        dy = target_center_y - image_center_y

        # Нормализуем в диапазон [-1, 1]
        normalized_dx = dx / (frame_width / 2.0)
        normalized_dy = dy / (frame_height / 2.0)

        # Вычисляем угловые скорости для поворота дрона
        # Предполагаем, что смещение на 10% кадра = поворот на 10% от FOV
        yaw_rate = normalized_dx * self.fov_horizontal * 0.5  # Угловая скорость поворота (рад/с)
        pitch_rate = -normalized_dy * self.fov_vertical * 0.5  # Угловая скорость наклона (рад/с)

        # Вычисляем расстояние до цели (приблизительно по размеру bbox)
        # Чем больше bbox, тем ближе цель
        bbox_area = w * h
        frame_area = frame_width * frame_height
        relative_size = bbox_area / frame_area

        # Целевое расстояние: ~5 метров от цели
        # Оцениваем расстояние по размеру цели в кадре
        # На расстоянии 5м цель (лицо/человек) занимает ~3-5% кадра
        # На расстоянии 7-8м цель занимает ~2-3% кадра
        # На расстоянии 3м цель занимает ~5-8% кадра
        target_size_min = 0.03  # Минимальный размер для расстояния ~5-6м (3% кадра)
        target_size_max = 0.04  # Максимальный размер для расстояния ~4-5м (4% кадра)
        too_close_size = 0.05   # Слишком близко, если больше 5% кадра (~3м)

        # Команда для приближения/отдаления с учетом целевого расстояния ~5 метров
        forward_velocity = 0.0
        if relative_size < target_size_min:
            # Цель слишком маленькая (далеко, >6м) - можно медленно приближаться
            forward_velocity = 0.15  # Медленное приближение
        elif relative_size > too_close_size:
            # Цель слишком большая (близко, <3м) - активно отдаляемся для безопасности
            forward_velocity = -0.4  # Увеличенная скорость отдаления
        elif relative_size > target_size_max:
            # Цель немного больше целевого размера (3-5м) - медленно отдаляемся
            forward_velocity = -0.2  # Медленное отдаление
        else:
            # В целевой зоне (4-6м) - поддерживаем расстояние
            forward_velocity = 0.0

        # Команда для вертикального движения - удерживаем цель в центре по вертикали
        # Используем pitch_rate для компенсации вертикального смещения
        vertical_velocity = pitch_rate * 0.5  # Преобразуем угловую скорость в вертикальную

        # Команда для бокового движения - следуем за целью, если она уходит в сторону
        # Если цель смещается в сторону, двигаемся в том же направлении
        # Используем комбинацию поворота и бокового движения для плавного следования
        lateral_velocity = 0.0
        if abs(normalized_dx) > 0.1:  # Если смещение больше 10% кадра
            # Двигаемся в сторону цели для более плавного следования
            lateral_velocity = normalized_dx * 0.3  # Боковое движение пропорционально смещению

        return {
            'linear_x': forward_velocity,
            'linear_y': lateral_velocity,  # Боковое движение для следования за целью
            'linear_z': vertical_velocity,  # Вертикальное движение для удержания цели в центре
            'angular_z': yaw_rate  # Поворот для удержания цели в центре
        }

    def get_target_position_in_frame(self) -> Optional[Point]:
        """Возвращает позицию цели в кадре в нормализованных координатах.

        Returns:
            Точка с координатами [0-1] или None
        """
        if not self.is_tracking or self.current_bbox is None:
            return None

        x, y, w, h = self.current_bbox

        # Нормализованные координаты центра цели
        point = Point()
        point.x = (x + w / 2.0) / (self.image_center_x * 2.0)  # Нормализовано к [-1, 1]
        point.y = (y + h / 2.0) / (self.image_center_y * 2.0)  # Нормализовано к [-1, 1]
        point.z = w * h / (self.image_center_x * self.image_center_y * 4.0)  # Относительный размер

        return point

    def stop_tracking(self):
        """Останавливает отслеживание."""
        self.is_tracking = False
        self.tracker = None
        self.current_bbox = None
        self.tracked_target_id = None

    def is_target_lost(self) -> bool:
        """Проверяет, потеряна ли цель."""
        return not self.is_tracking
