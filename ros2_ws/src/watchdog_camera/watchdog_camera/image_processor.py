"""Модуль обработки изображений.

Поддерживает различные эффекты и обработку изображений.
"""

import cv2
import numpy as np
from rclpy.logging import get_logger


class ImageProcessor:
    """Класс для обработки изображений."""

    def __init__(self):
        """Инициализирует процессор изображений."""
        self.logger = get_logger("ImageProcessor")

    def resize(self, image: np.ndarray, width: int, height: int) -> np.ndarray:
        """Изменяет размер изображения.

        Args:
            image: Исходное изображение
            width: Новая ширина
            height: Новая высота

        Returns:
            Измененное изображение
        """
        return cv2.resize(image, (width, height))

    def crop(self, image: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Обрезает изображение.

        Args:
            image: Исходное изображение
            x: X координата начала
            y: Y координата начала
            width: Ширина обрезки
            height: Высота обрезки

        Returns:
            Обрезанное изображение
        """
        return image[y : y + height, x : x + width]

    def rotate(self, image: np.ndarray, angle: float) -> np.ndarray:
        """Поворачивает изображение.

        Args:
            image: Исходное изображение
            angle: Угол поворота (градусы)

        Returns:
            Повернутое изображение
        """
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(image, matrix, (w, h))

    def adjust_brightness(self, image: np.ndarray, value: float) -> np.ndarray:
        """Изменяет яркость изображения.

        Args:
            image: Исходное изображение
            value: Значение изменения (-1.0 до 1.0)

        Returns:
            Изображение с измененной яркостью
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        v = cv2.add(v, np.full_like(v, int(value * 255)))
        v = np.clip(v, 0, 255).astype(np.uint8)
        hsv = cv2.merge([h, s, v])
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    def adjust_contrast(self, image: np.ndarray, alpha: float) -> np.ndarray:
        """Изменяет контрастность изображения.

        Args:
            image: Исходное изображение
            alpha: Коэффициент контрастности (1.0 = без изменений)

        Returns:
            Изображение с измененной контрастностью
        """
        return cv2.convertScaleAbs(image, alpha=alpha, beta=0)

    def apply_undistort(self, image: np.ndarray, camera_matrix: np.ndarray, dist_coeffs: np.ndarray) -> np.ndarray:
        """Убирает искажения камеры (требует калибровки).

        Args:
            image: Исходное изображение
            camera_matrix: Матрица камеры (3x3)
            dist_coeffs: Коэффициенты искажения

        Returns:
            Исправленное изображение
        """
        h, w = image.shape[:2]
        new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(camera_matrix, dist_coeffs, (w, h), 1, (w, h))
        return cv2.undistort(image, camera_matrix, dist_coeffs, None, new_camera_matrix)

    def detect_faces(self, image: np.ndarray) -> list:
        """Обнаруживает лица на изображении (для интеграции с face_detection).

        Args:
            image: Исходное изображение

        Returns:
            Список координат лиц [(x, y, w, h), ...]
        """
        # Используем простой детектор OpenCV
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")  # type: ignore[attr-defined]
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]
        except Exception as e:
            self.logger.warn(f"Ошибка детекции лиц: {e}")
            return []

    def draw_face_boxes(self, image: np.ndarray, faces: list) -> np.ndarray:
        """Рисует рамки вокруг лиц.

        Args:
            image: Исходное изображение
            faces: Список координат лиц

        Returns:
            Изображение с отмеченными лицами
        """
        result = image.copy()
        for x, y, w, h in faces:
            cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return result
