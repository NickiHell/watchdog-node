"""Улучшенное логирование для WatchDog."""

import logging
from rclpy.logging import get_logger as rclpy_get_logger
from rclpy.node import Node


class StructuredLogger:
    """Структурированный логгер с поддержкой контекста."""

    def __init__(self, name: str, node: Node | None = None):
        """Инициализирует структурированный логгер.

        Args:
            name: Имя логгера
            node: ROS2 узел (опционально)
        """
        self.name = name
        self.node = node
        self.ros_logger = rclpy_get_logger(name) if node is None else node.get_logger()
        self.context = {}

    def set_context(self, **kwargs):
        """Устанавливает контекст для логирования.

        Args:
            **kwargs: Пары ключ-значение для контекста
        """
        self.context.update(kwargs)

    def clear_context(self):
        """Очищает контекст."""
        self.context.clear()

    def _format_message(self, message: str, **kwargs) -> str:
        """Форматирует сообщение с контекстом.

        Args:
            message: Сообщение
            **kwargs: Дополнительные параметры

        Returns:
            Отформатированное сообщение
        """
        context_str = ""
        if self.context:
            context_items = [f"{k}={v}" for k, v in self.context.items()]
            context_str = f" [{', '.join(context_items)}]"

        kwargs_str = ""
        if kwargs:
            kwargs_items = [f"{k}={v}" for k, v in kwargs.items()]
            kwargs_str = f" ({', '.join(kwargs_items)})"

        return f"{message}{context_str}{kwargs_str}"

    def debug(self, message: str, **kwargs):
        """Логирует debug сообщение."""
        formatted = self._format_message(message, **kwargs)
        self.ros_logger.debug(formatted)

    def info(self, message: str, **kwargs):
        """Логирует info сообщение."""
        formatted = self._format_message(message, **kwargs)
        self.ros_logger.info(formatted)

    def warn(self, message: str, **kwargs):
        """Логирует warning сообщение."""
        formatted = self._format_message(message, **kwargs)
        self.ros_logger.warn(formatted)

    def error(self, message: str, **kwargs):
        """Логирует error сообщение."""
        formatted = self._format_message(message, **kwargs)
        self.ros_logger.error(formatted)

    def fatal(self, message: str, **kwargs):
        """Логирует fatal сообщение."""
        formatted = self._format_message(message, **kwargs)
        self.ros_logger.fatal(formatted)


def get_logger(name: str, node: Node | None = None) -> StructuredLogger:
    """Получает структурированный логгер.

    Args:
        name: Имя логгера
        node: ROS2 узел (опционально)

    Returns:
        StructuredLogger экземпляр
    """
    return StructuredLogger(name, node)


def setup_logging(level: str = "INFO"):
    """Настраивает логирование.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARN, ERROR, FATAL)
    """
    # Настройка стандартного Python logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
