"""Валидатор конфигурации для WatchDog."""

import yaml
from typing import Any
from pathlib import Path
import os


class ConfigValidationError(Exception):
    """Исключение для ошибок валидации конфигурации."""


class ConfigValidator:
    """Валидатор конфигурационных файлов."""

    def __init__(self, schema: dict[str, Any] | None = None):
        """Инициализирует валидатор.

        Args:
            schema: Схема валидации (опционально)
        """
        self.schema = schema or self._get_default_schema()
        self.errors: list[str] = []

    def _get_default_schema(self) -> dict[str, Any]:
        """Возвращает схему валидации по умолчанию.

        Returns:
            Словарь со схемой
        """
        return {
            "lidar": {
                "required": True,
                "type": dict,
                "schema": {
                    "device": {"type": str, "required": True},
                    "baudrate": {"type": int, "required": True, "min": 9600, "max": 256000},
                    "frame_id": {"type": str, "required": True},
                },
            },
            "camera": {
                "required": True,
                "type": dict,
                "schema": {
                    "frame_id": {"type": str, "required": False},
                    "topic": {"type": str, "required": False},
                    "siyi": {
                        "type": dict,
                        "required": True,
                        "schema": {
                            "ip": {"type": str, "required": True},
                            "port": {"type": int, "required": True, "min": 1, "max": 65535},
                            "stream_port": {"type": int, "required": True, "min": 1, "max": 65535},
                        },
                    },
                },
            },
            "pixhawk": {
                "required": True,
                "type": dict,
                "schema": {
                    "port": {"type": str, "required": True},
                    "baudrate": {"type": int, "required": True, "min": 9600, "max": 1152000},
                    "fcu_url": {"type": str, "required": True},
                },
            },
            "rc": {
                "required": False,
                "type": dict,
                "schema": {
                    "enabled": {"type": bool, "required": True},
                    "override_threshold": {"type": int, "required": False},
                    "deadzone": {"type": int, "required": False},
                },
            },
        }

    def validate(self, config: dict[str, Any]) -> bool:
        """Валидирует конфигурацию.

        Args:
            config: Словарь с конфигурацией

        Returns:
            True если конфигурация валидна

        Raises:
            ConfigValidationError: Если конфигурация невалидна
        """
        self.errors.clear()

        for key, schema in self.schema.items():
            if schema.get("required", False) and key not in config:
                self.errors.append(f"Отсутствует обязательный параметр: {key}")
                continue

            if key in config:
                self._validate_field(key, config[key], schema)

        if self.errors:
            error_msg = "Ошибки валидации конфигурации:\n" + "\n".join(f"  - {e}" for e in self.errors)
            raise ConfigValidationError(error_msg)

        return True

    def _validate_field(self, field_name: str, value: Any, schema: dict[str, Any]):
        """Валидирует поле конфигурации.

        Args:
            field_name: Имя поля
            value: Значение поля
            schema: Схема валидации
        """
        expected_type = schema.get("type")
        if expected_type and not isinstance(value, expected_type):
            self.errors.append(f"{field_name}: ожидается тип {expected_type.__name__}, получен {type(value).__name__}")
            return

        if expected_type == dict and "schema" in schema:
            # Рекурсивная валидация вложенных словарей
            for sub_key, sub_schema in schema["schema"].items():
                if sub_schema.get("required", False) and sub_key not in value:
                    self.errors.append(f"{field_name}.{sub_key}: обязательное поле отсутствует")
                elif sub_key in value:
                    self._validate_field(f"{field_name}.{sub_key}", value[sub_key], sub_schema)

        # Проверка диапазонов для числовых значений
        if isinstance(value, (int, float)):
            if "min" in schema and value < schema["min"]:
                self.errors.append(f"{field_name}: значение {value} меньше минимума {schema['min']}")
            if "max" in schema and value > schema["max"]:
                self.errors.append(f"{field_name}: значение {value} больше максимума {schema['max']}")

        # Проверка допустимых значений
        if "allowed" in schema and value not in schema["allowed"]:
            self.errors.append(f"{field_name}: значение {value} не в списке допустимых: {schema['allowed']}")

    @staticmethod
    def load_and_validate(config_path: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
        """Загружает и валидирует конфигурацию из файла.

        Args:
            config_path: Путь к файлу конфигурации
            schema: Схема валидации (опционально)

        Returns:
            Валидированная конфигурация

        Raises:
            ConfigValidationError: Если конфигурация невалидна
            FileNotFoundError: Если файл не найден
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {config_path}")

        with open(config_file, encoding="utf-8") as f:
            config = yaml.safe_load(f)

        if config is None:
            raise ConfigValidationError("Конфигурационный файл пуст")

        # Подстановка переменных окружения
        config = ConfigValidator._substitute_env_vars(config)

        validator = ConfigValidator(schema)
        validator.validate(config)

        return config

    @staticmethod
    def _substitute_env_vars(config: Any) -> Any:
        """Подставляет переменные окружения в конфигурацию.

        Поддерживает формат: ${VAR_NAME} или ${VAR_NAME:default_value}

        Args:
            config: Конфигурация (может быть вложенной)

        Returns:
            Конфигурация с подставленными переменными
        """
        if isinstance(config, dict):
            return {k: ConfigValidator._substitute_env_vars(v) for k, v in config.items()}
        if isinstance(config, list):
            return [ConfigValidator._substitute_env_vars(item) for item in config]
        if isinstance(config, str):
            # Поддержка ${VAR} и ${VAR:default}
            import re

            pattern = r"\$\{([^}:]+)(?::([^}]*))?\}"

            def replace_var(match):
                var_name = match.group(1)
                default_value = match.group(2) if match.group(2) else None
                return os.getenv(var_name, default_value or "")

            return re.sub(pattern, replace_var, config)
        return config
