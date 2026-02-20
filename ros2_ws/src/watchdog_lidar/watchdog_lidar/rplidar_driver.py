"""Драйвер для RPLidar S2.

RPLidar S2: дальность 30 м, 32000 точек/сек, UART 1 000 000 бод.
Размещается на PETG-мачте +120 мм над верхней платой дрона.
"""

import math
import serial
import struct
import time

from watchdog_lidar.lidar_base import LidarDriver, LidarScan


class RPLidarDriver(LidarDriver):
    """Драйвер для RPLidar S2."""

    SYNC_BYTE = 0xA5
    SYNC_BYTE2 = 0x5A

    CMD_STOP = 0x25
    CMD_RESET = 0x40
    CMD_SCAN = 0x20
    CMD_EXPRESS_SCAN = 0x82
    CMD_GET_INFO = 0x50
    CMD_GET_HEALTH = 0x52

    DESCRIPTOR_LEN = 7
    TYPE_SCAN = 0x81
    TYPE_EXPRESS_SCAN = 0x82

    # RPLidar S2 express scan: пакеты по 84 байта, содержат 32 кабины (cabin)
    EXPRESS_PACKET_SIZE = 84
    EXPRESS_CABIN_COUNT = 32

    def __init__(
        self,
        port: str,
        baudrate: int = 1000000,  # S2 требует 1 000 000 бод
        timeout: float = 1.0,
        mast_mask_sectors: list[list[float]] | None = None,
    ):
        """Инициализирует драйвер RPLidar S2.

        Args:
            port: Путь к последовательному порту
            baudrate: 1000000 для RPLidar S2
            timeout: Таймаут операций
            mast_mask_sectors: Список угловых секторов [start_rad, end_rad] для маскирования мачты
        """
        super().__init__(port, baudrate)
        self.timeout = timeout
        self.serial: serial.Serial | None = None
        self.scanning = False
        self.express_mode = True  # S2 использует express scan по умолчанию
        self.last_scan_time = 0.0
        # Сектора маски мачты (список пар [start_rad, end_rad])
        self.mast_mask_sectors: list[list[float]] = mast_mask_sectors or []

    def connect(self) -> bool:
        """Подключается к RPLidar S2."""
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )
            self.serial.reset_input_buffer()

            health = self._get_health()
            if health:
                self.logger.info(f"RPLidar S2 подключен, состояние: {health}")
            else:
                self.logger.warn("Не удалось проверить состояние RPLidar S2")

            self.is_connected = True
            return True

        except Exception as e:
            self.logger.error(f"Ошибка подключения к RPLidar S2: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        """Отключается от RPLidar."""
        if self.scanning:
            self.stop_scanning()
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.is_connected = False
        self.logger.info("Отключено от RPLidar S2")

    def start_scanning(self) -> bool:
        """Начинает сканирование в Express Scan Mode."""
        if not self.is_connected:
            self.logger.error("Не подключено к лидару")
            return False

        try:
            if self.scanning:
                self.stop_scanning()
                time.sleep(0.1)

            # Express Scan: 0x82 + payload [working_mode=0, reserved=0x00×4]
            self._send_command_with_payload(self.CMD_EXPRESS_SCAN, bytes([0x00, 0x00, 0x00, 0x00, 0x00]))
            time.sleep(0.1)

            descriptor = self._read_response_descriptor()
            if descriptor:
                self.scanning = True
                self.express_mode = True
                self.logger.info("RPLidar S2: Express Scan Mode запущен")
                return True

            # Fallback: стандартный скан
            self._send_command(self.CMD_SCAN)
            time.sleep(0.1)
            descriptor = self._read_response_descriptor()
            if descriptor:
                self.scanning = True
                self.express_mode = False
                self.logger.warn("RPLidar S2: использует стандартный Scan Mode (fallback)")
                return True

            self.logger.error("Не удалось запустить сканирование RPLidar S2")
            return False

        except Exception as e:
            self.logger.error(f"Ошибка запуска сканирования: {e}")
            return False

    def stop_scanning(self):
        """Останавливает сканирование."""
        if not self.scanning:
            return
        try:
            self._send_command(self.CMD_STOP)
            time.sleep(0.1)
            self.scanning = False
        except Exception as e:
            self.logger.error(f"Ошибка остановки сканирования: {e}")

    def get_scan(self) -> LidarScan | None:
        """Получает текущий скан и применяет маску мачты."""
        if not self.scanning or not self.serial:
            return None

        try:
            scan = LidarScan()
            scan.timestamp = time.time()

            if self.express_mode:
                ranges, angles, intensities = self._read_express_scan_packet()
            else:
                ranges, angles, intensities = self._read_standard_scan_packet()

            if not ranges:
                return None

            # Применяем программную маску угловых секторов мачты
            if self.mast_mask_sectors:
                ranges, angles, intensities = self._apply_mast_mask(ranges, angles, intensities)

            scan.ranges = ranges
            scan.angles = angles
            scan.intensities = intensities
            return scan

        except Exception as e:
            self.logger.debug(f"Ошибка чтения скана: {e}")
            return None

    def set_mast_mask_sectors(self, sectors: list[list[float]]):
        """Устанавливает угловые сектора маски мачты.

        Args:
            sectors: Список пар [start_rad, end_rad] в радианах [0, 2π]
        """
        self.mast_mask_sectors = sectors
        self.logger.info(f"Маска мачты обновлена: {len(sectors)} секторов")

    def get_info(self) -> dict:
        """Получает информацию об устройстве."""
        if not self.is_connected:
            return {}
        try:
            self._send_command(self.CMD_GET_INFO)
            time.sleep(0.1)
            descriptor = self._read_response_descriptor()
            if not descriptor:
                return {}

            data = self.serial.read(20)
            if len(data) < 20:
                return {}

            model = data[0]
            firmware_minor = data[1]
            firmware_major = data[2]
            hardware = data[3]
            serial_number = data[4:20].hex()

            return {
                "model": model,
                "firmware": f"{firmware_major}.{firmware_minor}",
                "hardware": hardware,
                "serial": serial_number,
            }
        except Exception as e:
            self.logger.error(f"Ошибка получения информации: {e}")
            return {}

    # ─── Приватные методы ──────────────────────────────────────────────────

    def _send_command(self, cmd: int):
        """Отправляет простую команду без payload."""
        if self.serial:
            self.serial.write(bytes([self.SYNC_BYTE, cmd]))

    def _send_command_with_payload(self, cmd: int, payload: bytes):
        """Отправляет команду с payload (размер + данные + контрольная сумма)."""
        if not self.serial:
            return
        size = len(payload)
        checksum = 0x00
        checksum ^= self.SYNC_BYTE
        checksum ^= cmd
        checksum ^= size
        for b in payload:
            checksum ^= b
        packet = bytes([self.SYNC_BYTE, cmd, size]) + payload + bytes([checksum])
        self.serial.write(packet)

    def _read_response_descriptor(self) -> dict | None:
        """Читает 7-байтный дескриптор ответа RPLidar."""
        if not self.serial:
            return None

        # Ищем стартовые байты 0xA5 0x5A
        buf = bytearray()
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            b = self.serial.read(1)
            if not b:
                continue
            buf.append(b[0])
            if len(buf) >= 2 and buf[-2] == self.SYNC_BYTE and buf[-1] == self.SYNC_BYTE2:
                break
        else:
            return None

        rest = self.serial.read(5)
        if len(rest) < 5:
            return None

        data_response_len = struct.unpack("<I", rest[0:4])[0] & 0x3FFFFFFF
        send_mode = (struct.unpack("<I", rest[0:4])[0] >> 30) & 0x03
        data_type = rest[4]

        return {
            "data_len": data_response_len,
            "send_mode": send_mode,
            "data_type": data_type,
        }

    def _read_standard_scan_packet(self) -> tuple[list[float], list[float], list[float]]:
        """Читает один пакет стандартного скана (5 байт/точка)."""
        if not self.serial:
            return [], [], []

        # Накапливаем до нового полного оборота (start bit)
        points: list = []
        while True:
            raw = self.serial.read(5)
            if len(raw) < 5:
                break

            quality = raw[0] >> 2
            start_flag = raw[0] & 0x01
            check_bit = raw[1] & 0x01

            angle_q6 = (raw[1] >> 1) | (raw[2] << 7)
            angle = angle_q6 / 64.0  # градусы

            distance_q2 = raw[3] | (raw[4] << 8)
            distance = distance_q2 / 4000.0  # метры

            if check_bit != 1:
                continue

            if start_flag and points:
                # Новый оборот — отдаём накопленные точки
                return self._points_to_arrays(points)

            if distance > 0.05 and quality > 0:
                points.append((math.radians(angle % 360), distance, float(quality)))

        return self._points_to_arrays(points)

    def _read_express_scan_packet(self) -> tuple[list[float], list[float], list[float]]:
        """Читает один пакет Express Scan (84 байта, 32 кабины × 2 точки).

        Формат пакета S2 Ultra (тот же, что у A2/A3):
          Байты 0-1: sync1/sync2 + checksum nibbles
          Байты 2-3: start_angle_q6 (15 бит) + new_scan flag (1 бит)
          Байты 4-83: 80 байт × 32 кабины (по 2.5 байта каждая)
        """
        if not self.serial:
            return [], [], []

        # Ищем заголовок пакета (0xA, 0x5)
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            b = self.serial.read(1)
            if not b:
                continue
            if b[0] == 0xA5:
                b2 = self.serial.read(1)
                if b2 and b2[0] == 0x5A:
                    break
        else:
            return [], [], []

        # Читаем оставшиеся 82 байта (84 - 2 стартовых)
        rest = self.serial.read(82)
        if len(rest) < 82:
            return [], [], []

        packet = rest

        (packet[0] >> 4) & 0x0F
        packet[0] & 0x0F
        start_angle_q6 = struct.unpack("<H", packet[2:4])[0] & 0x7FFF
        (struct.unpack("<H", packet[2:4])[0] >> 15) & 0x01
        start_angle = start_angle_q6 / 64.0  # градусы

        points = self._parse_express_cabins(start_angle, packet[4:])
        return self._points_to_arrays(points)

    def _parse_express_cabins(self, start_angle: float, cabin_data: bytes) -> list[tuple[float, float, float]]:
        """Разбирает 32 кабины express scan пакета.

        Каждая кабина: 5 байт → 2 точки:
          dist1 (14 бит), d_angle1 (4 бит signed), dist2 (14 бит), d_angle2 (4 бит signed)
        """
        points = []
        angle_step = 360.0 / (self.EXPRESS_CABIN_COUNT * 2)  # ~5.625° на точку

        for i in range(self.EXPRESS_CABIN_COUNT):
            offset = i * 5
            if offset + 5 > len(cabin_data):
                break

            b0, b1, b2, b3, b4 = cabin_data[offset : offset + 5]

            dist1 = ((b1 & 0x7F) << 8 | b0) >> 2
            dist2 = ((b3 & 0x7F) << 8 | b2) >> 2

            # d_angle: 4-битное знаковое (дополнение до двух)
            d_angle1_raw = ((b1 & 0x80) >> 4) | (b0 & 0x0F)
            d_angle2_raw = ((b3 & 0x80) >> 4) | (b2 & 0x0F)
            d_angle1 = d_angle1_raw if d_angle1_raw < 8 else d_angle1_raw - 16
            d_angle2 = d_angle2_raw if d_angle2_raw < 8 else d_angle2_raw - 16

            angle1 = (start_angle + (i * 2) * angle_step - d_angle1 / 2.0) % 360.0
            angle2 = (start_angle + (i * 2 + 1) * angle_step - d_angle2 / 2.0) % 360.0

            dist1_m = dist1 / 1000.0
            dist2_m = dist2 / 1000.0

            if dist1_m > 0.05:
                points.append((math.radians(angle1), dist1_m, 255.0))
            if dist2_m > 0.05:
                points.append((math.radians(angle2), dist2_m, 255.0))

        return points

    def _apply_mast_mask(
        self,
        ranges: list[float],
        angles: list[float],
        intensities: list[float],
    ) -> tuple[list[float], list[float], list[float]]:
        """Удаляет точки в секторах мачты (фиксированные препятствия самого дрона).

        Args:
            mast_mask_sectors: список пар [start_rad, end_rad] в [0, 2π]
        """
        filtered_ranges = []
        filtered_angles = []
        filtered_intensities = []

        for r, a, i in zip(ranges, angles, intensities):
            # Нормируем угол в [0, 2π]
            a_norm = a % (2 * math.pi)
            masked = False
            for sector in self.mast_mask_sectors:
                s_start, s_end = sector[0], sector[1]
                if s_start <= a_norm <= s_end:
                    masked = True
                    break
            if not masked:
                filtered_ranges.append(r)
                filtered_angles.append(a)
                filtered_intensities.append(i)

        return filtered_ranges, filtered_angles, filtered_intensities

    def _points_to_arrays(
        self, points: list[tuple[float, float, float]]
    ) -> tuple[list[float], list[float], list[float]]:
        """Преобразует список (angle, range, intensity) в три массива."""
        if not points:
            return [], [], []
        angles, ranges, intensities = zip(*points)
        return list(ranges), list(angles), list(intensities)

    def _get_health(self) -> str | None:
        """Читает статус устройства."""
        try:
            self._send_command(self.CMD_GET_HEALTH)
            time.sleep(0.1)
            descriptor = self._read_response_descriptor()
            if not descriptor:
                return None

            data = self.serial.read(3)
            if len(data) < 3:
                return None

            status = data[0]
            error_code = struct.unpack("<H", data[1:3])[0]
            status_map = {0: "OK", 1: "WARNING", 2: "ERROR"}
            result = status_map.get(status, "UNKNOWN")
            if error_code:
                result += f" (err=0x{error_code:04X})"
            return result

        except Exception:
            return None
