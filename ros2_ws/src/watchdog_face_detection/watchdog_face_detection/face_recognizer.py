"""Модуль распознавания лиц.

Создает эмбеддинги лиц для сравнения и распознавания.
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import rclpy
from rclpy.logging import get_logger


class FaceRecognizer:
    """Класс для создания эмбеддингов лиц."""

    def __init__(self, method: str = 'face_recognition'):
        """Инициализирует распознаватель лиц.

        Args:
            method: Метод распознавания ('face_recognition', 'insightface')
        """
        self.method = method.lower()
        self.logger = get_logger('FaceRecognizer')
        self.recognizer = None
        self._initialize_recognizer()

    def _initialize_recognizer(self):
        """Инициализирует распознаватель."""
        try:
            if self.method == 'face_recognition':
                self._init_face_recognition()
            elif self.method == 'insightface':
                self._init_insightface()
            else:
                raise ValueError(f'Неизвестный метод распознавания: {self.method}')
        except Exception as e:
            self.logger.error(f'Ошибка инициализации распознавателя: {e}')
            self.recognizer = None

    def _init_face_recognition(self):
        """Инициализирует face_recognition (рекомендуется для начала)."""
        try:
            import face_recognition

            self.recognizer = face_recognition
            self.logger.info('Face recognition инициализирован')

        except ImportError:
            self.logger.error(
                'Библиотека face_recognition не установлена. '
                'Установите: pip install face_recognition'
            )
            raise

    def _init_insightface(self):
        """Инициализирует InsightFace (более современный, требует настройки)."""
        try:
            import insightface

            # Загружаем модель (требует скачивания)
            self.recognizer = insightface.app.FaceAnalysis()
            self.recognizer.prepare(ctx_id=-1, det_size=(640, 640))
            self.logger.info('InsightFace инициализирован')

        except ImportError:
            self.logger.error(
                'Библиотека insightface не установлена. '
                'Установите: pip install insightface onnxruntime onnxruntime-gpu'
            )
            raise

    def encode_face(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Создает эмбеддинг лица.

        Args:
            face_image: Изображение лица (RGB или BGR)

        Returns:
            Эмбеддинг (вектор чисел) или None
        """
        if self.recognizer is None:
            self.logger.warn('Распознаватель не инициализирован')
            return None

        try:
            if self.method == 'face_recognition':
                return self._encode_face_recognition(face_image)
            elif self.method == 'insightface':
                return self._encode_insightface(face_image)
            return None
        except Exception as e:
            self.logger.error(f'Ошибка создания эмбеддинга: {e}')
            return None

    def _encode_face_recognition(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Создает эмбеддинг через face_recognition."""
        # Конвертируем в RGB если нужно
        if len(face_image.shape) == 3:
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = face_image

        # face_recognition требует определенный размер лица
        # Увеличиваем размер если слишком маленькое
        height, width = rgb_image.shape[:2]
        if width < 40 or height < 40:
            rgb_image = cv2.resize(rgb_image, (200, 200))

        # Получаем эмбеддинг
        encodings = self.recognizer.face_encodings(rgb_image)

        if len(encodings) == 0:
            self.logger.debug('Лицо не найдено на изображении для кодирования')
            return None

        # Возвращаем первый эмбеддинг (если несколько лиц, берем первое)
        return np.array(encodings[0])

    def _encode_insightface(self, face_image: np.ndarray) -> Optional[np.ndarray]:
        """Создает эмбеддинг через InsightFace."""
        # Конвертируем в RGB
        if len(face_image.shape) == 3:
            rgb_image = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        else:
            rgb_image = face_image

        # Получаем эмбеддинги
        faces = self.recognizer.get(rgb_image)

        if len(faces) == 0:
            self.logger.debug('Лицо не найдено на изображении')
            return None

        # Возвращаем эмбеддинг первого лица
        return faces[0].embedding

    def compare_faces(self, encoding1: np.ndarray, encoding2: np.ndarray, tolerance: float = 0.6) -> Tuple[bool, float]:
        """Сравнивает два эмбеддинга лиц.

        Args:
            encoding1: Первый эмбеддинг
            encoding2: Второй эмбеддинг
            tolerance: Порог схожести (ниже = строже, для face_recognition обычно 0.6)

        Returns:
            Кортеж (is_match, distance):
            - is_match: True если лица совпадают
            - distance: Расстояние между эмбеддингами
        """
        if encoding1 is None or encoding2 is None:
            return False, float('inf')

        if self.method == 'face_recognition':
            # face_recognition использует евклидово расстояние
            distance = np.linalg.norm(encoding1 - encoding2)
            is_match = distance <= tolerance
            return is_match, float(distance)
        else:
            # Для других методов используем косинусное расстояние
            similarity = self._cosine_similarity(encoding1, encoding2)
            distance = 1.0 - similarity
            is_match = distance <= tolerance
            return is_match, float(distance)

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Вычисляет косинусное сходство между векторами.

        Args:
            vec1: Первый вектор
            vec2: Второй вектор

        Returns:
            Сходство (0.0 - 1.0)
        """
        # Нормализуем векторы
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)

        # Вычисляем косинусное сходство
        similarity = np.dot(vec1_norm, vec2_norm)
        return float(np.clip(similarity, 0.0, 1.0))

