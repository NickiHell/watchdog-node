"""Тесты для обработки ошибок."""

import pytest
from watchdog_common.error_handling import (
    retry,
    RetryConfig,
    RetryStrategy,
    ErrorHandler,
    safe_execute,
    GracefulDegradation,
)


class TestRetry:
    """Тесты для retry механизма."""

    def test_retry_success(self):
        """Тест успешного выполнения без retry."""
        call_count = 0

        @retry(RetryConfig(max_attempts=3))
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 1

    def test_retry_with_failure(self):
        """Тест retry при ошибках."""
        call_count = 0

        @retry(RetryConfig(max_attempts=3, initial_delay=0.1))
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = test_func()
        assert result == "success"
        assert call_count == 3

    def test_retry_exhausted(self):
        """Тест исчерпания попыток."""

        @retry(RetryConfig(max_attempts=2, initial_delay=0.1))
        def test_func():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            test_func()

    def test_retry_strategies(self):
        """Тест различных стратегий задержки."""
        config_linear = RetryConfig(strategy=RetryStrategy.LINEAR, initial_delay=1.0)
        config_exp = RetryConfig(strategy=RetryStrategy.EXPONENTIAL, initial_delay=1.0)
        config_fixed = RetryConfig(strategy=RetryStrategy.FIXED, initial_delay=1.0)

        assert config_linear.calculate_delay(1) == 1.0
        assert config_linear.calculate_delay(2) == 2.0
        assert config_linear.calculate_delay(3) == 3.0

        assert config_exp.calculate_delay(1) == 1.0
        assert config_exp.calculate_delay(2) == 2.0
        assert config_exp.calculate_delay(3) == 4.0

        assert config_fixed.calculate_delay(1) == 1.0
        assert config_fixed.calculate_delay(2) == 1.0
        assert config_fixed.calculate_delay(3) == 1.0


class TestErrorHandler:
    """Тесты для ErrorHandler."""

    def test_error_handler_with_fallback(self):
        """Тест обработчика с fallback."""
        handler = ErrorHandler()

        def fallback_func(error, *args, **kwargs):
            return "fallback_result"

        handler.register_fallback(ValueError, fallback_func)

        def failing_func():
            raise ValueError("Error")

        result = handler.handle(failing_func)
        assert result == "fallback_result"

    def test_error_handler_no_fallback(self):
        """Тест обработчика без fallback."""
        handler = ErrorHandler()

        def failing_func():
            raise ValueError("Error")

        with pytest.raises(ValueError):
            handler.handle(failing_func)


class TestSafeExecute:
    """Тесты для safe_execute."""

    def test_safe_execute_success(self):
        """Тест успешного выполнения."""

        def test_func():
            return "success"

        result = safe_execute(test_func, default="default")
        assert result == "success"

    def test_safe_execute_with_error(self):
        """Тест выполнения с ошибкой."""

        def test_func():
            raise ValueError("Error")

        result = safe_execute(test_func, default="default")
        assert result == "default"


class TestGracefulDegradation:
    """Тесты для GracefulDegradation."""

    def test_feature_management(self):
        """Тест управления функциями."""
        gd = GracefulDegradation()

        gd.register_feature("lidar", enabled=True)
        assert gd.is_feature_enabled("lidar") is True

        gd.disable_feature("lidar", reason="Device not found")
        assert gd.is_feature_enabled("lidar") is False

        gd.enable_feature("lidar")
        assert gd.is_feature_enabled("lidar") is True
