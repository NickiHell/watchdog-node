"""Универсальный драйвер для лидаров с неизвестным протоколом.

Используется для экспериментов с MOP3 и другими лидарами.
Пытается автоматически определить формат данных.
"""

import serial
import struct
import time
from typing import Optional, List, Tuple
import numpy as np

from watchdog_lidar.lidar_base import LidarDriver, LidarScan


class GenericLidarDriver(LidarDriver):
    """Универсальный драйвер для лидаров с неизвестным протоколом."""

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 1.0,
        data_format: str = 'auto'
    ):
        """Инициализирует универсальный драйвер.

        Args:
            port: Путь к последовательному порту
            baudrate: Скорость передачи
            timeout: Таймаут операций
            data_format: Формат данных ('auto', 'hex', 'binary')
        """
        super().__init__(port, baudrate)
        self.timeout = timeout
        self.data_format = data_format
        self.serial: Optional[serial.Serial] = None
        self.scanning = False
        self.raw_buffer = bytearray()

    def connect(self) -> bool:
        """Подключается к лидару."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )

            self.serial.reset_input_buffer()
            self.is_connected = True
            self.logger.info(f'Подключено к лидару на {self.port}')
            return True

        except Exception as e:
            self.logger.error(f'Ошибка подключения: {e}')
            self.is_connected = False
            return False

    def disconnect(self):
        """Отключается от лидара."""
        if self.scanning:
            self.stop_scanning()

        if self.serial and self.serial.is_open:
            self.serial.close()

        self.is_connected = False

    def start_scanning(self) -> bool:
        """Начинает сканирование."""
        if not self.is_connected:
            return False

        self.scanning = True
        self.raw_buffer.clear()
        self.logger.info('Сканирование начато (generic mode)')
        return True

    def stop_scanning(self):
        """Останавливает сканирование."""
        self.scanning = False
        self.raw_buffer.clear()

    def get_scan(self) -> Optional[LidarScan]:
        """Получает текущий скан.

        Пытается автоматически определить формат данных.
        """
        if not self.scanning or not self.serial:
            return None

        try:
            # Читаем доступные данные
            available = self.serial.in_waiting
            if available > 0:
                data = self.serial.read(available)
                self.raw_buffer.extend(data)

            # Пытаемся найти паттерны в данных
            scan = self._try_parse_data()
            return scan

        except Exception as e:
            self.logger.debug(f'Ошибка чтения данных: {e}')
            return None

    def get_info(self) -> dict:
        """Получает информацию о лидаре."""
        return {
            'driver': 'generic',
            'port': self.port,
            'baudrate': self.baudrate,
            'note': 'Протокол автоматически определяется'
        }

    def _try_parse_data(self) -> Optional[LidarScan]:
        """Пытается распарсить данные, пробуя разные форматы."""
        if len(self.raw_buffer) < 100:  # Нужно достаточно данных
            return None

        # Стратегия 1: Ищем паттерны синхронизации (0xAA, 0x55 и т.д.)
        # Стратегия 2: Пытаемся интерпретировать как массив расстояний
        # Стратегия 3: Ищем структуру с заголовком

        # Простая эвристика: если данные выглядят как последовательность чисел
        # Пробуем интерпретировать как расстояния через фиксированные углы

        try:
            # Пробуем интерпретировать каждые 2 байта как uint16 расстояние
            ranges = []
            angles = []
            intensities = []

            step = 2
            point_count = len(self.raw_buffer) // step
            angle_step = 2.0 * np.pi / point_count if point_count > 0 else 0.0

            for i in range(min(point_count, 360)):  # Максимум 360 точек
                offset = i * step
                if offset + step > len(self.raw_buffer):
                    break

                # Читаем как little-endian uint16
                distance_raw = struct.unpack('<H', self.raw_buffer[offset:offset + step])[0]

                # Конвертируем в метры (предполагаем разные масштабы)
                distance = distance_raw / 1000.0  # Попробуем масштаб 1/1000
                angle = i * angle_step

                # Фильтруем разумные значения
                if 0.05 < distance < 12.0:
                    ranges.append(distance)
                    angles.append(angle)
                    intensities.append(100.0)  # По умолчанию

            if len(ranges) > 10:  # Минимум точек для валидного скана
                scan = LidarScan()
                scan.ranges = ranges
                scan.angles = angles
                scan.intensities = intensities
                scan.timestamp = time.time()

                # Очищаем буфер после успешного парсинга
                self.raw_buffer.clear()
                return scan

        except Exception:
            pass

        # Если не получилось, очищаем часть буфера чтобы не переполнить
        if len(self.raw_buffer) > 10000:
            self.raw_buffer = self.raw_buffer[-5000:]

        return None

    def send_raw_command(self, command: bytes) -> bool:
        """Отправляет сырую команду лидару (для экспериментов).

        Args:
            command: Байты команды

        Returns:
            True если успешно отправлено
        """
        if not self.serial or not self.serial.is_open:
            return False

        try:
            self.serial.write(command)
            self.logger.info(f'Отправлена команда: {command.hex()}')
            return True
        except Exception as e:
            self.logger.error(f'Ошибка отправки команды: {e}')
            return False

    def read_raw_data(self, size: int = 1024) -> bytes:
        """Читает сырые данные с лидара (для анализа).

        Args:
            size: Количество байт для чтения

        Returns:
            Байты данных
        """
        if not self.serial or not self.serial.is_open:
            return b''

        try:
            return self.serial.read(size)
        except Exception:
            return b''

