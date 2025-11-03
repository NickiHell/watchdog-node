"""Протокол связи со STM32.

Реализует протокол обмена данными между ROS2 и STM32 микроконтроллером.
Формат сообщений:
- Заголовок: [0xAA, 0x55]
- Тип команды: 1 байт
- Данные: N байт
- Контрольная сумма: XOR всех байт
"""

import struct
from enum import IntEnum
from typing import Optional


class CommandType(IntEnum):
    """Типы команд для STM32."""

    MOVEMENT = 0x01  # Команда движения (cmd_vel)
    STATUS_REQUEST = 0x02  # Запрос состояния
    PARAM_SET = 0x03  # Установка параметров


class ResponseType(IntEnum):
    """Типы ответов от STM32."""

    ERROR = 0x10  # Ошибка
    SUCCESS = 0x11  # Успех
    ENCODER_DATA = 0x12  # Данные энкодеров


class ProtocolError(Exception):
    """Исключение для ошибок протокола."""

    pass


class STM32Protocol:
    """Класс для работы с протоколом связи STM32."""

    HEADER_BYTE_1 = 0xAA
    HEADER_BYTE_2 = 0x55

    @staticmethod
    def calculate_checksum(data: bytes) -> int:
        """Вычисляет контрольную сумму (XOR всех байт).

        Args:
            data: Байты данных для вычисления контрольной суммы

        Returns:
            Контрольная сумма (1 байт)
        """
        checksum = 0
        for byte in data:
            checksum ^= byte
        return checksum & 0xFF

    @staticmethod
    def encode_movement_command(linear_x: float, angular_z: float) -> bytes:
        """Кодирует команду движения в байты.

        Формат:
        - Заголовок: [0xAA, 0x55]
        - Тип команды: 0x01
        - linear.x: float (32-bit, little-endian)
        - angular.z: float (32-bit, little-endian)
        - Контрольная сумма: 1 байт

        Args:
            linear_x: Линейная скорость (м/с)
            angular_z: Угловая скорость (рад/с)

        Returns:
            Байтовая строка с командой
        """
        command_type = CommandType.MOVEMENT
        payload = struct.pack('<f', linear_x) + struct.pack('<f', angular_z)

        # Формируем пакет без контрольной суммы
        packet = bytes([STM32Protocol.HEADER_BYTE_1, STM32Protocol.HEADER_BYTE_2, command_type]) + payload

        # Вычисляем и добавляем контрольную сумму
        checksum = STM32Protocol.calculate_checksum(packet)
        packet += bytes([checksum])

        return packet

    @staticmethod
    def encode_status_request() -> bytes:
        """Кодирует запрос состояния.

        Returns:
            Байтовая строка с запросом
        """
        command_type = CommandType.STATUS_REQUEST
        packet = bytes([STM32Protocol.HEADER_BYTE_1, STM32Protocol.HEADER_BYTE_2, command_type])
        checksum = STM32Protocol.calculate_checksum(packet)
        packet += bytes([checksum])
        return packet

    @staticmethod
    def decode_response(data: bytes) -> dict:
        """Декодирует ответ от STM32.

        Args:
            data: Байты ответа от STM32

        Returns:
            Словарь с декодированными данными:
            {
                'type': ResponseType,
                'valid': bool,
                'data': bytes или dict с распарсенными данными
            }

        Raises:
            ProtocolError: Если данные некорректны
        """
        if len(data) < 4:
            raise ProtocolError(f'Слишком короткий ответ: {len(data)} байт (минимум 4)')

        # Проверяем заголовок
        if data[0] != STM32Protocol.HEADER_BYTE_1 or data[1] != STM32Protocol.HEADER_BYTE_2:
            raise ProtocolError(f'Неверный заголовок: {data[0]:02X} {data[1]:02X}')

        response_type = data[2]
        payload = data[3:-1]  # Все данные кроме заголовка, типа и контрольной суммы
        received_checksum = data[-1]

        # Проверяем контрольную сумму
        packet_without_checksum = data[:-1]
        calculated_checksum = STM32Protocol.calculate_checksum(packet_without_checksum)

        if received_checksum != calculated_checksum:
            raise ProtocolError(
                f'Ошибка контрольной суммы: получено {received_checksum:02X}, '
                f'вычислено {calculated_checksum:02X}'
            )

        result = {
            'type': ResponseType(response_type),
            'valid': True,
            'data': payload,
        }

        # Парсим специфичные данные в зависимости от типа ответа
        if response_type == ResponseType.ENCODER_DATA:
            result['parsed_data'] = STM32Protocol._parse_encoder_data(payload)
        elif response_type == ResponseType.SUCCESS:
            result['parsed_data'] = {'status': 'OK'}
        elif response_type == ResponseType.ERROR:
            error_code = payload[0] if payload else 0
            result['parsed_data'] = {'error_code': error_code}

        return result

    @staticmethod
    def _parse_encoder_data(data: bytes) -> dict:
        """Парсит данные энкодеров.

        Ожидаемый формат:
        - encoder_left: int32 (4 байта, little-endian)
        - encoder_right: int32 (4 байта, little-endian)
        - timestamp_ms: uint32 (4 байта, little-endian) - опционально

        Args:
            data: Байты данных энкодеров

        Returns:
            Словарь с распарсенными данными
        """
        if len(data) < 8:
            return {'encoder_left': 0, 'encoder_right': 0, 'timestamp_ms': 0}

        encoder_left = struct.unpack('<i', data[0:4])[0]
        encoder_right = struct.unpack('<i', data[4:8])[0]
        timestamp_ms = struct.unpack('<I', data[8:12])[0] if len(data) >= 12 else 0

        return {
            'encoder_left': encoder_left,
            'encoder_right': encoder_right,
            'timestamp_ms': timestamp_ms,
        }

    @staticmethod
    def find_packet_start(data: bytes, start_pos: int = 0) -> Optional[int]:
        """Находит начало пакета в потоке данных.

        Args:
            data: Байты данных
            start_pos: Позиция начала поиска

        Returns:
            Индекс начала пакета или None если не найдено
        """
        for i in range(start_pos, len(data) - 1):
            if data[i] == STM32Protocol.HEADER_BYTE_1 and data[i + 1] == STM32Protocol.HEADER_BYTE_2:
                return i
        return None

