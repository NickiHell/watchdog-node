"""Утилиты безопасности для WatchDog."""

import re
from typing import Optional, List
from pathlib import Path


class SecurityValidator:
    """Валидатор безопасности для входных данных."""

    @staticmethod
    def validate_device_path(path: str) -> bool:
        """Валидирует путь к устройству.

        Args:
            path: Путь к устройству

        Returns:
            True если путь безопасен
        """
        # Разрешаем только стандартные пути к устройствам
        allowed_patterns = [
            r'^/dev/tty(USB|ACM)\d+$',  # /dev/ttyUSB0, /dev/ttyACM0
            r'^/dev/video\d+$',  # /dev/video0
        ]

        for pattern in allowed_patterns:
            if re.match(pattern, path):
                return True

        return False

    @staticmethod
    def sanitize_string(value: str, max_length: int = 256) -> Optional[str]:
        """Очищает строку от потенциально опасных символов.

        Args:
            value: Строка для очистки
            max_length: Максимальная длина

        Returns:
            Очищенная строка или None если невалидна
        """
        if not isinstance(value, str):
            return None

        # Удаляем null байты и другие опасные символы
        sanitized = value.replace('\x00', '').replace('\r', '')

        # Ограничиваем длину
        if len(sanitized) > max_length:
            return None

        return sanitized

    @staticmethod
    def validate_command_range(value: float, min_val: float, max_val: float) -> bool:
        """Валидирует диапазон команды.

        Args:
            value: Значение команды
            min_val: Минимальное значение
            max_val: Максимальное значение

        Returns:
            True если значение в допустимом диапазоне
        """
        return min_val <= value <= max_val

    @staticmethod
    def validate_file_path(path: str, allowed_dirs: Optional[List[str]] = None) -> bool:
        """Валидирует путь к файлу.

        Args:
            path: Путь к файлу
            allowed_dirs: Список разрешенных директорий

        Returns:
            True если путь безопасен
        """
        try:
            file_path = Path(path).resolve()

            # Проверка на path traversal
            if '..' in str(file_path):
                return False

            # Если указаны разрешенные директории
            if allowed_dirs:
                for allowed_dir in allowed_dirs:
                    allowed_path = Path(allowed_dir).resolve()
                    try:
                        file_path.relative_to(allowed_path)
                        return True
                    except ValueError:
                        continue
                return False

            return True
        except Exception:
            return False

    @staticmethod
    def validate_port(port: int) -> bool:
        """Валидирует номер порта.

        Args:
            port: Номер порта

        Returns:
            True если порт валиден
        """
        return 1 <= port <= 65535

    @staticmethod
    def validate_baudrate(baudrate: int) -> bool:
        """Валидирует скорость передачи.

        Args:
            baudrate: Скорость передачи

        Returns:
            True если скорость валидна
        """
        # Стандартные скорости передачи
        allowed_baudrates = [
            9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 256000
        ]
        return baudrate in allowed_baudrates

