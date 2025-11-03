"""Драйвер для RPLidar (A1, A2, A3).

RPLidar - популярный и хорошо документированный лидар.
Поддерживает модели A1, A2, A3 через стандартный протокол.
"""

import serial
import struct
import time
from typing import Optional, List, Tuple
import numpy as np

from watchdog_lidar.lidar_base import LidarDriver, LidarScan


class RPLidarDriver(LidarDriver):
    """Драйвер для RPLidar."""

    # Константы протокола RPLidar
    SYNC_BYTE = 0xA5
    SYNC_BYTE2 = 0x5A

    # Команды
    CMD_STOP = 0x25
    CMD_RESET = 0x40
    CMD_SCAN = 0x20
    CMD_EXPRESS_SCAN = 0x82  # Для A2
    CMD_GET_INFO = 0x50
    CMD_GET_HEALTH = 0x52

    # Типы дескрипторов
    DESCRIPTOR_LEN = 5
    TYPE_SCAN = 0x81
    TYPE_EXPRESS_SCAN = 0x82

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 1.0):
        """Инициализирует драйвер RPLidar.

        Args:
            port: Путь к последовательному порту
            baudrate: Скорость передачи (115200 для A1/A2, 256000 для A3)
            timeout: Таймаут операций
        """
        super().__init__(port, baudrate)
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.scanning = False
        self.express_mode = False  # Для A2/A3
        self.last_scan_time = 0.0

    def connect(self) -> bool:
        """Подключается к RPLidar."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )

            # Очищаем буфер
            self.serial.reset_input_buffer()

            # Проверяем здоровье лидара
            health = self._get_health()
            if health:
                self.logger.info(f'RPLidar подключен, здоровье: {health}')
            else:
                self.logger.warn('Не удалось проверить здоровье лидара')

            self.is_connected = True
            return True

        except Exception as e:
            self.logger.error(f'Ошибка подключения к RPLidar: {e}')
            self.is_connected = False
            return False

    def disconnect(self):
        """Отключается от RPLidar."""
        if self.scanning:
            self.stop_scanning()

        if self.serial and self.serial.is_open:
            self.serial.close()

        self.is_connected = False
        self.logger.info('Отключено от RPLidar')

    def start_scanning(self) -> bool:
        """Начинает сканирование."""
        if not self.is_connected:
            self.logger.error('Не подключено к лидару')
            return False

        try:
            # Останавливаем предыдущее сканирование если было
            if self.scanning:
                self.stop_scanning()
                time.sleep(0.1)

            # Отправляем команду сканирования
            self._send_command(self.CMD_SCAN)
            time.sleep(0.1)

            # Читаем дескриптор
            descriptor = self._read_descriptor()
            if descriptor:
                self.scanning = True
                self.logger.info('Сканирование начато')
                return True
            else:
                self.logger.error('Не удалось начать сканирование')
                return False

        except Exception as e:
            self.logger.error(f'Ошибка запуска сканирования: {e}')
            return False

    def stop_scanning(self):
        """Останавливает сканирование."""
        if not self.scanning:
            return

        try:
            self._send_command(self.CMD_STOP)
            time.sleep(0.1)
            self.scanning = False
            self.logger.info('Сканирование остановлено')
        except Exception as e:
            self.logger.error(f'Ошибка остановки сканирования: {e}')

    def get_scan(self) -> Optional[LidarScan]:
        """Получает текущий скан."""
        if not self.scanning or not self.serial:
            return None

        try:
            scan = LidarScan()
            scan.timestamp = time.time()

            # Читаем дескриптор
            descriptor = self._read_descriptor()
            if not descriptor:
                return None

            # Читаем данные скана
            data_length = descriptor['length'] - 2
            data = self.serial.read(data_length)

            if len(data) != data_length:
                return None

            # Парсим данные в зависимости от типа
            if descriptor['type'] == self.TYPE_SCAN:
                ranges, angles, intensities = self._parse_scan_data(data)
            elif descriptor['type'] == self.TYPE_EXPRESS_SCAN:
                ranges, angles, intensities = self._parse_express_scan_data(data)
            else:
                return None

            scan.ranges = ranges
            scan.angles = angles
            scan.intensities = intensities

            return scan

        except Exception as e:
            self.logger.debug(f'Ошибка чтения скана: {e}')
            return None

    def get_info(self) -> dict:
        """Получает информацию о лидаре."""
        if not self.is_connected:
            return {}

        try:
            self._send_command(self.CMD_GET_INFO)
            time.sleep(0.1)

            descriptor = self._read_descriptor()
            if not descriptor:
                return {}

            data_length = descriptor['length'] - 2
            data = self.serial.read(data_length)

            if len(data) < 20:
                return {}

            # Парсим информацию
            model = data[0]
            firmware_minor = data[1]
            firmware_major = data[2]
            hardware = data[3]
            serial_number = struct.unpack('16s', data[4:20])[0]

            return {
                'model': model,
                'firmware': f'{firmware_major}.{firmware_minor}',
                'hardware': hardware,
                'serial': serial_number.decode('utf-8', errors='ignore').strip('\x00'),
            }

        except Exception as e:
            self.logger.error(f'Ошибка получения информации: {e}')
            return {}

    def _send_command(self, cmd: int):
        """Отправляет команду лидару."""
        if not self.serial:
            return

        # Формат команды: [SYNC_BYTE] [CMD]
        command = bytes([self.SYNC_BYTE, cmd])
        self.serial.write(command)

    def _read_descriptor(self) -> Optional[dict]:
        """Читает дескриптор пакета."""
        if not self.serial:
            return None

        # Ищем синхронизационный байт
        while True:
            byte = self.serial.read(1)
            if not byte:
                return None

            if byte[0] == self.SYNC_BYTE:
                break

        # Читаем остальные байты дескриптора
        descriptor_data = self.serial.read(self.DESCRIPTOR_LEN - 1)
        if len(descriptor_data) != self.DESCRIPTOR_LEN - 1:
            return None

        # Парсим дескриптор
        descriptor = {
            'sync': self.SYNC_BYTE,
            'type': descriptor_data[0],
            'length': struct.unpack('<H', descriptor_data[1:3])[0],
            'checksum': struct.unpack('<H', descriptor_data[3:5])[0],
        }

        return descriptor

    def _parse_scan_data(self, data: bytes) -> Tuple[List[float], List[float], List[float]]:
        """Парсит данные обычного скана."""
        ranges = []
        angles = []
        intensities = []

        # Каждый скан содержит 5 байт на точку
        point_count = len(data) // 5

        for i in range(point_count):
            offset = i * 5
            if offset + 5 > len(data):
                break

            # Формат: [distance_low] [distance_high] [angle_low] [angle_high] [quality]
            distance = struct.unpack('<H', data[offset:offset + 2])[0] / 4000.0  # В метрах
            angle_raw = struct.unpack('<H', data[offset + 2:offset + 4])[0]
            angle = (angle_raw >> 1) / 64.0  # В радианах
            quality = data[offset + 4]

            # Фильтруем невалидные точки
            if distance > 0.01 and quality > 0:
                ranges.append(distance)
                angles.append(angle)
                intensities.append(float(quality))

        return ranges, angles, intensities

    def _parse_express_scan_data(self, data: bytes) -> Tuple[List[float], List[float], List[float]]:
        """Парсит данные express скана (для A2/A3)."""
        ranges = []
        angles = []
        intensities = []

        # Express scan имеет другую структуру
        # Упрощенная версия - полный парсинг требует более сложной логики
        # Здесь возвращаем базовую структуру
        # Для полной реализации нужен более детальный разбор протокола

        return ranges, angles, intensities

    def _get_health(self) -> Optional[str]:
        """Получает статус здоровья лидара."""
        try:
            self._send_command(self.CMD_GET_HEALTH)
            time.sleep(0.1)

            descriptor = self._read_descriptor()
            if not descriptor:
                return None

            data = self.serial.read(descriptor['length'] - 2)
            if len(data) < 3:
                return None

            status = data[0]
            error_code = struct.unpack('<H', data[1:3])[0]

            status_map = {0: 'OK', 1: 'WARNING', 2: 'ERROR'}
            return status_map.get(status, 'UNKNOWN')

        except Exception:
            return None

