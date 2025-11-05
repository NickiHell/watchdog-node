"""Модуль детекции лиц.

Поддерживает различные методы детекции: OpenCV Haar, dlib HOG, face_recognition.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import rclpy
from rclpy.logging import get_logger


class FaceDetector:
    """Класс для детекции лиц на изображениях."""

    def __init__(self, method: str = 'face_recognition', model_path: Optional[str] = None):
        """Инициализирует детектор лиц.

        Args:
            method: Метод детекции ('haar', 'dlib', 'face_recognition', 'opencv_dnn')
            model_path: Путь к модели (для некоторых методов)
        """
        self.method = method.lower()
        self.model_path = model_path
        self.logger = get_logger('FaceDetector')
        self.detector = None
        self._initialize_detector()

    def _initialize_detector(self):
        """Инициализирует детектор."""
        try:
            if self.method == 'haar':
                self._init_haar()
            elif self.method == 'dlib':
                self._init_dlib()
            elif self.method == 'face_recognition':
                self._init_face_recognition()
            elif self.method == 'opencv_dnn':
                self._init_opencv_dnn()
            else:
                raise ValueError(f'Неизвестный метод детекции: {self.method}')
        except Exception as e:
            self.logger.error(f'Ошибка инициализации детектора: {e}')
            self.detector = None

    def _init_haar(self):
        """Инициализирует детектор Haar Cascade."""
        try:
            cascade_path = (
                self.model_path
                if self.model_path
                else cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )

            self.detector = cv2.CascadeClassifier(cascade_path)
            if self.detector.empty():
                raise ValueError(f'Не удалось загрузить каскад из {cascade_path}')
            self.logger.info(f'Haar Cascade загружен из {cascade_path}')

        except Exception as e:
            self.logger.error(f'Ошибка инициализации Haar: {e}')
            raise

    def _init_dlib(self):
        """Инициализирует детектор dlib HOG."""
        try:
            import dlib

            # model_path игнорируется для dlib - всегда используется встроенный детектор
            self.detector = dlib.get_frontal_face_detector()
            self.logger.info('Dlib HOG детектор загружен')

        except ImportError:
            self.logger.error('Библиотека dlib не установлена. Установите: pip install dlib')
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации dlib: {e}')
            raise

    def _init_face_recognition(self):
        """Инициализирует детектор face_recognition (рекомендуется)."""
        try:
            import face_recognition

            # face_recognition использует dlib под капотом
            self.detector = face_recognition
            self.logger.info('Face recognition детектор загружен')

        except ImportError:
            self.logger.error(
                'Библиотека face_recognition не установлена. '
                'Установите: pip install face_recognition'
            )
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации face_recognition: {e}')
            raise

    def _init_opencv_dnn(self):
        """Инициализирует детектор OpenCV DNN."""
        try:
            # Загружаем модель DNN для детекции лиц
            if not self.model_path:
                # Можно использовать предобученные модели из OpenCV или загрузить отдельно
                self.logger.warn('Путь к модели DNN не указан, используем Haar вместо DNN')
                self.method = 'haar'
                self._init_haar()
                return

            self.detector = cv2.dnn.readNetFromTensorflow(self.model_path)
            self.logger.info(f'OpenCV DNN модель загружена из {self.model_path}')

        except Exception as e:
            self.logger.error(f'Ошибка инициализации OpenCV DNN: {e}')
            raise

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Обнаруживает лица на изображении.

        Args:
            image: Изображение в формате numpy array (BGR или RGB)

        Returns:
            Список координат лиц [(x, y, width, height), ...]
        """
        if self.detector is None:
            self.logger.warn('Детектор не инициализирован')
            return []

        try:
            if self.method == 'haar':
                return self._detect_haar(image)
            elif self.method == 'dlib':
                return self._detect_dlib(image)
            elif self.method == 'face_recognition':
                return self._detect_face_recognition(image)
            elif self.method == 'opencv_dnn':
                return self._detect_opencv_dnn(image)
            else:
                return []

        except Exception as e:
            self.logger.error(f'Ошибка детекции лиц: {e}')
            return []

    def _detect_haar(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Детекция через Haar Cascade."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        faces = self.detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30)
        )
        return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    def _detect_dlib(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Детекция через dlib HOG."""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        detections = self.detector(rgb_image, 1)  # 1 = upsample factor
        faces = []
        for detection in detections:
            x = detection.left()
            y = detection.top()
            w = detection.width()
            h = detection.height()
            faces.append((int(x), int(y), int(w), int(h)))
        return faces

    def _detect_face_recognition(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Детекция через face_recognition."""
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image
        face_locations = self.detector.face_locations(rgb_image, model='hog')  # или 'cnn' для GPU
        faces = []
        for top, right, bottom, left in face_locations:
            x = left
            y = top
            w = right - left
            h = bottom - top
            faces.append((int(x), int(y), int(w), int(h)))
        return faces

    def _detect_opencv_dnn(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Детекция через OpenCV DNN (требует настройки модели)."""
        # Упрощенная реализация, требует полной настройки модели
        self.logger.warn('OpenCV DNN детекция требует дополнительной настройки')
        return []

    def extract_face_region(self, image: np.ndarray, face_box: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """Извлекает область лица из изображения.

        Args:
            image: Исходное изображение
            face_box: Координаты лица (x, y, width, height)

        Returns:
            Обрезанное изображение лица или None
        """
        x, y, w, h = face_box
        height, width = image.shape[:2]

        # Проверяем границы
        x = max(0, x)
        y = max(0, y)
        w = min(w, width - x)
        h = min(h, height - y)

        if w <= 0 or h <= 0:
            return None

        return image[y:y + h, x:x + w]

