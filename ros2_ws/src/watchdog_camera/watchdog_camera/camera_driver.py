"""Драйвер камеры SIYI A8 mini (захват по RTSP)."""

import cv2
import numpy as np
from rclpy.logging import get_logger


class SIYIDriver:
    """Драйвер захвата видео с SIYI A8 mini по RTSP."""

    def __init__(self, ip: str, stream_port: int = 8554, width: int = 1920, height: int = 1080, fps: int = 30):
        """Инициализирует драйвер SIYI.

        Args:
            ip: IP-адрес SIYI A8 mini в сети (например 192.168.144.25)
            stream_port: Порт RTSP-потока (обычно 8554 или 554)
            width: Ожидаемая ширина (для camera_info)
            height: Ожидаемая высота
            fps: Ожидаемый FPS
        """
        self.ip = ip
        self.stream_port = stream_port
        self.width = width
        self.height = height
        self.fps = fps
        self.logger = get_logger("SIYIDriver")
        self.cap: cv2.VideoCapture | None = None
        self.is_opened = False

    def _rtsp_url(self) -> str:
        """Формирует URL RTSP-потока SIYI."""
        return f"rtsp://{self.ip}:{self.stream_port}/stream1"

    def open(self) -> bool:
        """Открывает RTSP-поток с SIYI.

        Returns:
            True если поток успешно открыт
        """
        try:
            url = self._rtsp_url()
            self.cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)

            if not self.cap.isOpened():
                self.logger.error(f"Не удалось открыть RTSP поток: {url}")
                return False

            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or self.width)
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.height)
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS) or self.fps

            self.logger.info(f"SIYI RTSP открыт: {url} — {actual_width}x{actual_height} @ {actual_fps:.1f} FPS")
            self.is_opened = True
            return True

        except Exception as e:
            self.logger.error(f"Ошибка открытия SIYI RTSP: {e}")
            return False

    def close(self):
        """Закрывает поток."""
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_opened = False
        self.logger.info("SIYI камера закрыта")

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
        """Возвращает информацию о камере (для CameraInfo)."""
        if not self.cap:
            return {
                "width": self.width,
                "height": self.height,
                "fps": self.fps,
                "backend": "RTSP",
                "source": self._rtsp_url(),
            }

        try:
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or self.width)
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or self.height)
            fps = self.cap.get(cv2.CAP_PROP_FPS) or self.fps
            return {
                "width": width,
                "height": height,
                "fps": fps,
                "backend": "RTSP",
                "source": self._rtsp_url(),
            }
        except Exception:
            return {
                "width": self.width,
                "height": self.height,
                "fps": self.fps,
                "backend": "RTSP",
                "source": self._rtsp_url(),
            }
