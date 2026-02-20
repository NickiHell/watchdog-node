"""Модуль драйвера камеры.

Поддерживает USB камеры, Raspberry Pi Camera и несколько камер.
"""

import cv2
import numpy as np
from rclpy.logging import get_logger


class CameraDriver:
    """Базовый класс для работы с камерой."""

    def __init__(self, device_id: int = 0, width: int = 1920, height: int = 1080, fps: int = 30):
        """Инициализирует драйвер камеры.

        Args:
            device_id: ID устройства камеры или путь к устройству
            width: Ширина изображения
            height: Высота изображения
            fps: Частота кадров
        """
        self.device_id = device_id
        self.width = width
        self.height = height
        self.fps = fps
        self.logger = get_logger("CameraDriver")
        self.cap: cv2.VideoCapture | None = None
        self.is_opened = False

    def open(self) -> bool:
        """Открывает камеру.

        Returns:
            True если успешно открыто
        """
        try:
            self.cap = cv2.VideoCapture(self.device_id)

            if not self.cap.isOpened():
                self.logger.error(f"Не удалось открыть камеру {self.device_id}")
                return False

            # Устанавливаем параметры
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Проверяем реальные параметры
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)

            self.logger.info(f"Камера открыта: {actual_width}x{actual_height} @ {actual_fps} FPS")

            self.is_opened = True
            return True

        except Exception as e:
            self.logger.error(f"Ошибка открытия камеры: {e}")
            return False

    def close(self):
        """Закрывает камеру."""
        if self.cap:
            self.cap.release()
            self.is_opened = False
            self.logger.info("Камера закрыта")

    def read(self) -> np.ndarray | None:
        """Читает кадр с камеры.

        Returns:
            Кадр в формате numpy array (BGR) или None
        """
        if not self.is_opened or not self.cap:
            return None

        ret, frame = self.cap.read()
        if ret:
            return frame
        return None

    def get_info(self) -> dict:
        """Получает информацию о камере.

        Returns:
            Словарь с информацией
        """
        if not self.cap:
            return {}

        try:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            backend = self.cap.getBackendName()

            return {
                "width": width,
                "height": height,
                "fps": fps,
                "backend": backend,
                "device_id": self.device_id,
            }
        except Exception:
            return {}


class USBCameraDriver(CameraDriver):
    """Драйвер для USB камеры."""

    def __init__(self, device_id: int = 0, width: int = 1920, height: int = 1080, fps: int = 30):
        """Инициализирует USB камеру.

        Args:
            device_id: ID USB камеры (обычно 0, 1, 2...)
            width: Ширина
            height: Высота
            fps: Частота кадров
        """
        super().__init__(device_id, width, height, fps)
        self.camera_type = "usb"


class PiCameraDriver(CameraDriver):
    """Драйвер для Raspberry Pi Camera Module."""

    def __init__(self, width: int = 1920, height: int = 1080, fps: int = 30):
        """Инициализирует Raspberry Pi Camera.

        Args:
            width: Ширина
            height: Высота
            fps: Частота кадров
        """
        super().__init__(device_id=0, width=width, height=height, fps=fps)
        self.camera_type = "picamera"

    def open(self) -> bool:
        """Открывает Pi Camera."""
        try:
            # Для Pi Camera используем специальный backend
            # В Linux обычно это v4l2 через /dev/video0
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

            if not self.cap.isOpened():
                self.logger.error("Не удалось открыть Raspberry Pi Camera")
                return False

            # Устанавливаем параметры
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            # Для Pi Camera может потребоваться дополнительная настройка
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Минимизируем задержку

            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self.logger.info(f"Raspberry Pi Camera открыта: {actual_width}x{actual_height}")
            self.is_opened = True
            return True

        except Exception as e:
            self.logger.error(f"Ошибка открытия Pi Camera: {e}")
            return False


class MultiCameraDriver:
    """Драйвер для работы с несколькими камерами (360° эффект)."""

    def __init__(self, camera_ids: list[int], width: int = 1920, height: int = 1080, fps: int = 30):
        """Инициализирует драйвер для нескольких камер.

        Args:
            camera_ids: Список ID камер
            width: Ширина каждого изображения
            height: Высота каждого изображения
            fps: Частота кадров
        """
        self.camera_ids = camera_ids
        self.width = width
        self.height = height
        self.fps = fps
        self.logger = get_logger("MultiCameraDriver")
        self.cameras: list[CameraDriver] = []
        self.is_opened = False

    def open(self) -> bool:
        """Открывает все камеры.

        Returns:
            True если хотя бы одна камера открыта
        """
        success_count = 0
        for camera_id in self.camera_ids:
            camera = CameraDriver(camera_id, self.width, self.height, self.fps)
            if camera.open():
                self.cameras.append(camera)
                success_count += 1
                self.logger.info(f"Камера {camera_id} открыта")
            else:
                self.logger.warn(f"Не удалось открыть камеру {camera_id}")

        self.is_opened = success_count > 0
        if self.is_opened:
            self.logger.info(f"Открыто камер: {success_count}/{len(self.camera_ids)}")
        return self.is_opened

    def close(self):
        """Закрывает все камеры."""
        for camera in self.cameras:
            camera.close()
        self.cameras.clear()
        self.is_opened = False

    def read_all(self) -> list[np.ndarray | None]:
        """Читает кадры со всех камер.

        Returns:
            Список кадров (может содержать None для недоступных камер)
        """
        frames = []
        for camera in self.cameras:
            frame = camera.read()
            frames.append(frame)
        return frames

    def read_stitched(self) -> np.ndarray | None:
        """Читает кадры и склеивает их в панораму.

        Returns:
            Склеенное изображение или None
        """
        frames = self.read_all()
        valid_frames = [f for f in frames if f is not None]

        if len(valid_frames) == 0:
            return None

        if len(valid_frames) == 1:
            return valid_frames[0]

        # Простое склеивание горизонтально
        # Для более сложной склейки можно использовать OpenCV stitching
        try:
            stitched = np.hstack(valid_frames)
            return stitched
        except Exception as e:
            self.logger.error(f"Ошибка склейки изображений: {e}")
            return valid_frames[0] if valid_frames else None

    def get_info(self) -> list[dict]:
        """Получает информацию о всех камерах.

        Returns:
            Список словарей с информацией
        """
        info = []
        for camera in self.cameras:
            info.append(camera.get_info())
        return info
