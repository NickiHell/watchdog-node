"""Тесты для утилит безопасности."""

from watchdog_common.security import SecurityValidator


class TestSecurityValidator:
    """Тесты для SecurityValidator."""

    def test_validate_device_path(self):
        """Тест валидации пути к устройству."""
        assert SecurityValidator.validate_device_path("/dev/ttyUSB0") is True
        assert SecurityValidator.validate_device_path("/dev/ttyACM0") is True
        assert SecurityValidator.validate_device_path("/dev/video0") is True
        assert SecurityValidator.validate_device_path("/dev/ttyUSB") is False
        assert SecurityValidator.validate_device_path("/etc/passwd") is False
        assert SecurityValidator.validate_device_path("../../etc/passwd") is False

    def test_sanitize_string(self):
        """Тест очистки строки."""
        assert SecurityValidator.sanitize_string("test") == "test"
        assert SecurityValidator.sanitize_string("test\x00null") == "testnull"
        assert SecurityValidator.sanitize_string("a" * 300, max_length=256) is None
        assert SecurityValidator.sanitize_string("normal string") == "normal string"

    def test_validate_command_range(self):
        """Тест валидации диапазона команды."""
        assert SecurityValidator.validate_command_range(0.5, 0.0, 1.0) is True
        assert SecurityValidator.validate_command_range(-0.1, 0.0, 1.0) is False
        assert SecurityValidator.validate_command_range(1.1, 0.0, 1.0) is False

    def test_validate_file_path(self):
        """Тест валидации пути к файлу."""
        assert SecurityValidator.validate_file_path("/tmp/test.txt") is True
        assert SecurityValidator.validate_file_path("../../etc/passwd") is False
        assert SecurityValidator.validate_file_path("/tmp/test.txt", allowed_dirs=["/tmp"]) is True
        assert SecurityValidator.validate_file_path("/etc/passwd", allowed_dirs=["/tmp"]) is False

    def test_validate_port(self):
        """Тест валидации порта."""
        assert SecurityValidator.validate_port(8080) is True
        assert SecurityValidator.validate_port(65535) is True
        assert SecurityValidator.validate_port(1) is True
        assert SecurityValidator.validate_port(0) is False
        assert SecurityValidator.validate_port(65536) is False

    def test_validate_baudrate(self):
        """Тест валидации скорости передачи."""
        assert SecurityValidator.validate_baudrate(115200) is True
        assert SecurityValidator.validate_baudrate(9600) is True
        assert SecurityValidator.validate_baudrate(256000) is True
        assert SecurityValidator.validate_baudrate(12345) is False
        assert SecurityValidator.validate_baudrate(999999) is False
