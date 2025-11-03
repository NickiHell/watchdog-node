"""Интерфейс для работы с последовательным портом STM32."""

import serial
import serial.tools.list_ports
from typing import Optional
import rclpy
from rclpy.logging import get_logger


class SerialInterface:
    """Класс для работы с последовательным портом для связи со STM32."""

    def __init__(self, port: str, baudrate: int = 115200, timeout: float = 0.1):
        """Инициализирует последовательный порт.

        Args:
            port: Путь к последовательному порту (например, /dev/ttyACM0)
            baudrate: Скорость передачи (по умолчанию 115200)
            timeout: Таймаут чтения в секундах
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.logger = get_logger('SerialInterface')

    def connect(self) -> bool:
        """Открывает соединение с последовательным портом.

        Returns:
            True если соединение установлено успешно
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            self.logger.info(f'Подключено к {self.port} на скорости {self.baudrate}')
            return True
        except serial.SerialException as e:
            self.logger.error(f'Ошибка подключения к {self.port}: {e}')
            return False
        except Exception as e:
            self.logger.error(f'Неожиданная ошибка при подключении: {e}')
            return False

    def disconnect(self):
        """Закрывает соединение."""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.logger.info(f'Отключено от {self.port}')

    def send_command(self, command: bytes) -> bool:
        """Отправляет команду на STM32.

        Args:
            command: Байтовая строка с командой

        Returns:
            True если команда отправлена успешно
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            self.logger.warn('Последовательный порт не открыт')
            return False

        try:
            written = self.serial_connection.write(command)
            self.serial_connection.flush()
            if written != len(command):
                self.logger.warn(f'Отправлено только {written} из {len(command)} байт')
                return False
            return True
        except serial.SerialException as e:
            self.logger.error(f'Ошибка отправки данных: {e}')
            return False

    def read_response(self, max_bytes: int = 64) -> Optional[bytes]:
        """Читает ответ от STM32.

        Args:
            max_bytes: Максимальное количество байт для чтения

        Returns:
            Байты ответа или None в случае ошибки
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return None

        try:
            if self.serial_connection.in_waiting > 0:
                data = self.serial_connection.read(min(self.serial_connection.in_waiting, max_bytes))
                return data
            return None
        except serial.SerialException as e:
            self.logger.error(f'Ошибка чтения данных: {e}')
            return None

    def read_available(self) -> bytes:
        """Читает все доступные данные.

        Returns:
            Байты всех доступных данных
        """
        if not self.serial_connection or not self.serial_connection.is_open:
            return b''

        try:
            available = self.serial_connection.in_waiting
            if available > 0:
                return self.serial_connection.read(available)
            return b''
        except serial.SerialException as e:
            self.logger.error(f'Ошибка чтения данных: {e}')
            return b''

    def is_connected(self) -> bool:
        """Проверяет, открыто ли соединение.

        Returns:
            True если соединение открыто
        """
        return self.serial_connection is not None and self.serial_connection.is_open

    @staticmethod
    def list_available_ports() -> list:
        """Возвращает список доступных последовательных портов.

        Returns:
            Список кортежей (port, description)
        """
        ports = serial.tools.list_ports.comports()
        return [(port.device, port.description) for port in ports]

