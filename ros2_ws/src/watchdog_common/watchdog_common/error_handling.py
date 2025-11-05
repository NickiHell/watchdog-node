"""Обработка ошибок и retry механизмы для WatchDog."""

import time
import functools
from typing import Callable, TypeVar, Optional, List, Type, Dict
from enum import Enum
from rclpy.logging import get_logger

T = TypeVar('T')


class RetryStrategy(Enum):
    """Стратегии повторных попыток."""

    LINEAR = 'linear'  # Линейная задержка
    EXPONENTIAL = 'exponential'  # Экспоненциальная задержка
    FIXED = 'fixed'  # Фиксированная задержка


class RetryConfig:
    """Конфигурация для retry механизма."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_exceptions: Optional[List[Type[Exception]]] = None,
    ):
        """Инициализирует конфигурацию retry.

        Args:
            max_attempts: Максимальное количество попыток
            initial_delay: Начальная задержка (секунды)
            max_delay: Максимальная задержка (секунды)
            strategy: Стратегия задержки
            retryable_exceptions: Список исключений, при которых нужно повторять попытку
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = strategy
        self.retryable_exceptions = retryable_exceptions or [Exception]

    def calculate_delay(self, attempt: int) -> float:
        """Вычисляет задержку для попытки.

        Args:
            attempt: Номер попытки (начиная с 1)

        Returns:
            Задержка в секундах
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        else:  # EXPONENTIAL
            delay = self.initial_delay * (2 ** (attempt - 1))

        return min(delay, self.max_delay)


def retry(
    config: Optional[RetryConfig] = None,
    logger_name: Optional[str] = None,
):
    """Декоратор для автоматического retry.

    Args:
        config: Конфигурация retry
        logger_name: Имя логгера

    Returns:
        Декорированная функция

    Пример:
        @retry(RetryConfig(max_attempts=5, initial_delay=0.5))
        def connect_to_device():
            # код подключения
            pass
    """
    if config is None:
        config = RetryConfig()

    logger = get_logger(logger_name or 'Retry')

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(config.retryable_exceptions) as e:
                    last_exception = e
                    is_last_attempt = attempt >= config.max_attempts

                    if is_last_attempt:
                        logger.error(f'{func.__name__} failed after {config.max_attempts} attempts: {e}')
                    else:
                        delay = config.calculate_delay(attempt)
                        logger.warn(
                            f'{func.__name__} failed (attempt {attempt}/{config.max_attempts}): {e}. '
                            f'Retrying in {delay:.2f}s...'
                        )
                        time.sleep(delay)

            raise last_exception

        return wrapper

    return decorator


class ErrorHandler:
    """Обработчик ошибок с поддержкой fallback."""

    def __init__(self, logger_name: Optional[str] = None):
        """Инициализирует обработчик ошибок.

        Args:
            logger_name: Имя логгера
        """
        self.logger = get_logger(logger_name or 'ErrorHandler')
        self.fallback_handlers: Dict[Type[Exception], Callable] = {}

    def register_fallback(self, exception_type: Type[Exception], handler: Callable):
        """Регистрирует fallback обработчик для типа исключения.

        Args:
            exception_type: Тип исключения
            handler: Функция-обработчик
        """
        self.fallback_handlers[exception_type] = handler

    def handle(self, func: Callable[..., T], *args, **kwargs) -> Optional[T]:
        """Выполняет функцию с обработкой ошибок.

        Args:
            func: Функция для выполнения
            *args: Позиционные аргументы
            **kwargs: Именованные аргументы

        Returns:
            Результат функции или None при ошибке
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exception_type = type(e)
            if exception_type in self.fallback_handlers:
                self.logger.warn(f'Using fallback handler for {exception_type.__name__}: {e}')
                return self.fallback_handlers[exception_type](e, *args, **kwargs)
            else:
                self.logger.error(f'Unhandled exception in {func.__name__}: {e}')
                raise


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    logger_name: Optional[str] = None,
) -> Optional[T]:
    """Безопасно выполняет функцию, возвращая значение по умолчанию при ошибке.

    Args:
        func: Функция для выполнения
        default: Значение по умолчанию при ошибке
        logger_name: Имя логгера

    Returns:
        Результат функции или значение по умолчанию
    """
    logger = get_logger(logger_name or 'SafeExecute')

    try:
        return func()
    except Exception as e:
        logger.error(f'Error in {func.__name__}: {e}', exc_info=True)
        return default


class GracefulDegradation:
    """Менеджер graceful degradation."""

    def __init__(self, logger_name: Optional[str] = None):
        """Инициализирует менеджер.

        Args:
            logger_name: Имя логгера
        """
        self.logger = get_logger(logger_name or 'GracefulDegradation')
        self.features: Dict[str, bool] = {}

    def register_feature(self, name: str, enabled: bool = True):
        """Регистрирует функцию системы.

        Args:
            name: Имя функции
            enabled: Включена ли функция
        """
        self.features[name] = enabled

    def is_feature_enabled(self, name: str) -> bool:
        """Проверяет, включена ли функция.

        Args:
            name: Имя функции

        Returns:
            True если функция включена
        """
        return self.features.get(name, False)

    def disable_feature(self, name: str, reason: str = ''):
        """Отключает функцию.

        Args:
            name: Имя функции
            reason: Причина отключения
        """
        self.features[name] = False
        self.logger.warn(f'Feature {name} disabled. Reason: {reason}')

    def enable_feature(self, name: str):
        """Включает функцию.

        Args:
            name: Имя функции
        """
        self.features[name] = True
        self.logger.info(f'Feature {name} enabled')

