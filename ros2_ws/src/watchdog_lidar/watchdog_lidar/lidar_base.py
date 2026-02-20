"""Базовый класс для драйверов лидара."""

from abc import ABC, abstractmethod
from sensor_msgs.msg import LaserScan
from rclpy.logging import get_logger


class LidarScan:
    """Структура данных скана лидара."""

    def __init__(self):
        self.ranges: list[float] = []  # Расстояния в метрах
        self.angles: list[float] = []  # Углы в радианах
        self.intensities: list[float] = []  # Интенсивность (опционально)
        self.timestamp: float = 0.0  # Время скана

    def to_laserscan(self, frame_id: str = "lidar_frame") -> LaserScan:
        """Конвертирует в ROS2 LaserScan сообщение.

        Args:
            frame_id: Имя фрейма

        Returns:
            LaserScan сообщение
        """
        msg = LaserScan()
        msg.header.frame_id = frame_id
        msg.angle_min = min(self.angles) if self.angles else -3.14159
        msg.angle_max = max(self.angles) if self.angles else 3.14159
        msg.angle_increment = (
            (msg.angle_max - msg.angle_min) / (len(self.ranges) - 1) if len(self.ranges) > 1 else 0.0174533  # ~1 градус
        )
        msg.time_increment = 0.0
        msg.scan_time = 0.1  # 10 Hz по умолчанию
        msg.range_min = min(self.ranges) if self.ranges else 0.05
        msg.range_max = max(self.ranges) if self.ranges else 12.0
        msg.ranges = self.ranges
        msg.intensities = self.intensities if self.intensities else []
        return msg


class LidarDriver(ABC):
    """Базовый абстрактный класс для драйверов лидара."""

    def __init__(self, port: str, baudrate: int = 115200):
        """Инициализирует драйвер лидара.

        Args:
            port: Путь к последовательному порту
            baudrate: Скорость передачи
        """
        self.port = port
        self.baudrate = baudrate
        self.is_connected = False
        self.logger = get_logger(self.__class__.__name__)

    @abstractmethod
    def connect(self) -> bool:
        """Подключается к лидару.

        Returns:
            True если подключение успешно
        """

    @abstractmethod
    def disconnect(self):
        """Отключается от лидара."""

    @abstractmethod
    def start_scanning(self) -> bool:
        """Начинает сканирование.

        Returns:
            True если успешно
        """

    @abstractmethod
    def stop_scanning(self):
        """Останавливает сканирование."""

    @abstractmethod
    def get_scan(self) -> LidarScan | None:
        """Получает текущий скан.

        Returns:
            LidarScan или None если скан недоступен
        """

    @abstractmethod
    def get_info(self) -> dict:
        """Получает информацию о лидаре.

        Returns:
            Словарь с информацией
        """
