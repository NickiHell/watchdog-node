"""Unit тесты для протокола STM32."""

import pytest
from watchdog_stm32_interface.protocol import (
    STM32Protocol,
    CommandType,
    ResponseType,
    ProtocolError,
)


class TestSTM32Protocol:
    """Тесты для STM32Protocol."""

    def test_calculate_checksum(self):
        """Тест вычисления контрольной суммы."""
        data = bytes([0xAA, 0x55, 0x01])
        checksum = STM32Protocol.calculate_checksum(data)
        assert isinstance(checksum, int)
        assert 0 <= checksum <= 255

        # Проверка для известных значений
        data2 = bytes([0x01, 0x02, 0x03])
        checksum2 = STM32Protocol.calculate_checksum(data2)
        assert checksum2 == 0x00  # 0x01 ^ 0x02 ^ 0x03 = 0x00

    def test_encode_movement_command(self):
        """Тест кодирования команды движения."""
        linear_x = 0.5
        angular_z = 1.0
        packet = STM32Protocol.encode_movement_command(linear_x, angular_z)

        # Проверяем размер пакета (заголовок(2) + тип(1) + linear(4) + angular(4) + chksum(1))
        assert len(packet) == 12

        # Проверяем заголовок
        assert packet[0] == 0xAA
        assert packet[1] == 0x55

        # Проверяем тип команды
        assert packet[2] == CommandType.MOVEMENT

        # Проверяем контрольную сумму
        packet_without_checksum = packet[:-1]
        calculated_checksum = STM32Protocol.calculate_checksum(packet_without_checksum)
        assert packet[-1] == calculated_checksum

    def test_encode_status_request(self):
        """Тест кодирования запроса состояния."""
        packet = STM32Protocol.encode_status_request()

        # Проверяем размер (заголовок(2) + тип(1) + chksum(1))
        assert len(packet) == 4

        # Проверяем заголовок
        assert packet[0] == 0xAA
        assert packet[1] == 0x55

        # Проверяем тип команды
        assert packet[2] == CommandType.STATUS_REQUEST

        # Проверяем контрольную сумму
        packet_without_checksum = packet[:-1]
        calculated_checksum = STM32Protocol.calculate_checksum(packet_without_checksum)
        assert packet[-1] == calculated_checksum

    def test_decode_response_success(self):
        """Тест декодирования ответа SUCCESS."""
        # Создаем валидный ответ SUCCESS
        response_type = ResponseType.SUCCESS
        payload = b''
        packet = bytes([0xAA, 0x55, response_type]) + payload
        checksum = STM32Protocol.calculate_checksum(packet)
        packet += bytes([checksum])

        result = STM32Protocol.decode_response(packet)

        assert result['type'] == ResponseType.SUCCESS
        assert result['valid'] is True
        assert result['parsed_data']['status'] == 'OK'

    def test_decode_response_encoder_data(self):
        """Тест декодирования данных энкодеров."""
        import struct

        # Создаем валидный ответ с данными энкодеров
        response_type = ResponseType.ENCODER_DATA
        encoder_left = 1000
        encoder_right = 2000
        timestamp_ms = 12345

        payload = (
            struct.pack('<i', encoder_left) +
            struct.pack('<i', encoder_right) +
            struct.pack('<I', timestamp_ms)
        )

        packet = bytes([0xAA, 0x55, response_type]) + payload
        checksum = STM32Protocol.calculate_checksum(packet)
        packet += bytes([checksum])

        result = STM32Protocol.decode_response(packet)

        assert result['type'] == ResponseType.ENCODER_DATA
        assert result['valid'] is True
        assert result['parsed_data']['encoder_left'] == encoder_left
        assert result['parsed_data']['encoder_right'] == encoder_right
        assert result['parsed_data']['timestamp_ms'] == timestamp_ms

    def test_decode_response_error(self):
        """Тест декодирования ответа ERROR."""
        response_type = ResponseType.ERROR
        error_code = 0x42
        payload = bytes([error_code])

        packet = bytes([0xAA, 0x55, response_type]) + payload
        checksum = STM32Protocol.calculate_checksum(packet)
        packet += bytes([checksum])

        result = STM32Protocol.decode_response(packet)

        assert result['type'] == ResponseType.ERROR
        assert result['valid'] is True
        assert result['parsed_data']['error_code'] == error_code

    def test_decode_response_invalid_header(self):
        """Тест декодирования с неверным заголовком."""
        packet = bytes([0x00, 0x00, 0x11, 0x00])

        with pytest.raises(ProtocolError, match='Неверный заголовок'):
            STM32Protocol.decode_response(packet)

    def test_decode_response_invalid_checksum(self):
        """Тест декодирования с неверной контрольной суммой."""
        packet = bytes([0xAA, 0x55, 0x11, 0x99])  # Неверная контрольная сумма

        with pytest.raises(ProtocolError, match='Ошибка контрольной суммы'):
            STM32Protocol.decode_response(packet)

    def test_decode_response_too_short(self):
        """Тест декодирования слишком короткого ответа."""
        packet = bytes([0xAA])  # Слишком короткий

        with pytest.raises(ProtocolError, match='Слишком короткий ответ'):
            STM32Protocol.decode_response(packet)

    def test_find_packet_start(self):
        """Тест поиска начала пакета."""
        # Пакет начинается с середины
        data = bytes([0x00, 0x01, 0xAA, 0x55, 0x01, 0x02])
        pos = STM32Protocol.find_packet_start(data)
        assert pos == 2

        # Пакет в начале
        data2 = bytes([0xAA, 0x55, 0x01, 0x02])
        pos2 = STM32Protocol.find_packet_start(data2)
        assert pos2 == 0

        # Пакет не найден
        data3 = bytes([0x00, 0x01, 0x02, 0x03])
        pos3 = STM32Protocol.find_packet_start(data3)
        assert pos3 is None

        # Пакет с указанием начальной позиции
        data4 = bytes([0xAA, 0x55, 0x01, 0x00, 0xAA, 0x55, 0x02])
        pos4 = STM32Protocol.find_packet_start(data4, start_pos=4)
        assert pos4 == 4

