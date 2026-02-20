"""State machine для контроллера WatchDog."""

from enum import Enum
from collections.abc import Callable
from rclpy.logging import get_logger


class RobotMode(Enum):
    """Режимы работы дрона."""

    IDLE = "idle"  # Режим ожидания
    NAVIGATION = "navigation"  # Навигация к цели
    TRACKING = "tracking"  # Отслеживание цели
    TAKEOFF = "takeoff"  # Взлет
    LANDING = "landing"  # Посадка
    HOVERING = "hovering"  # Зависание
    ERROR = "error"  # Режим ошибки
    EMERGENCY_STOP = "emergency_stop"  # Аварийная остановка


class StateMachine:
    """Конечный автомат для управления режимами дрона."""

    def __init__(self, initial_mode: RobotMode = RobotMode.IDLE):
        """Инициализирует state machine.

        Args:
            initial_mode: Начальный режим работы
        """
        self.current_mode = initial_mode
        self.previous_mode: RobotMode | None = None
        self.logger = get_logger("StateMachine")
        self.on_mode_change_callbacks: list[Callable] = []

    def transition_to(self, new_mode: RobotMode) -> bool:
        """Переходит в новый режим.

        Args:
            new_mode: Новый режим

        Returns:
            True если переход успешен
        """
        if self.current_mode == new_mode:
            return True

        # Проверяем валидность перехода
        if not self._is_valid_transition(self.current_mode, new_mode):
            self.logger.warn(f"Недопустимый переход: {self.current_mode.value} -> {new_mode.value}")
            return False

        # Выполняем переход
        self.previous_mode = self.current_mode
        self.current_mode = new_mode

        self.logger.info(f"Переход режима: {self.previous_mode.value} -> {self.current_mode.value}")

        # Вызываем callbacks
        for callback in self.on_mode_change_callbacks:
            try:
                callback(self.previous_mode, self.current_mode)
            except Exception as e:
                self.logger.error(f"Ошибка в callback перехода режима: {e}")

        return True

    def _is_valid_transition(self, from_mode: RobotMode, to_mode: RobotMode) -> bool:
        """Проверяет валидность перехода между режимами.

        Args:
            from_mode: Исходный режим
            to_mode: Целевой режим

        Returns:
            True если переход допустим
        """
        # Разрешенные переходы для дрона
        valid_transitions = {
            RobotMode.IDLE: [RobotMode.NAVIGATION, RobotMode.TRACKING, RobotMode.TAKEOFF, RobotMode.ERROR],
            RobotMode.TAKEOFF: [RobotMode.HOVERING, RobotMode.NAVIGATION, RobotMode.ERROR, RobotMode.EMERGENCY_STOP],
            RobotMode.NAVIGATION: [
                RobotMode.IDLE,
                RobotMode.TRACKING,
                RobotMode.HOVERING,
                RobotMode.LANDING,
                RobotMode.ERROR,
                RobotMode.EMERGENCY_STOP,
            ],
            RobotMode.TRACKING: [
                RobotMode.IDLE,
                RobotMode.NAVIGATION,
                RobotMode.HOVERING,
                RobotMode.ERROR,
                RobotMode.EMERGENCY_STOP,
            ],
            RobotMode.HOVERING: [
                RobotMode.IDLE,
                RobotMode.NAVIGATION,
                RobotMode.TRACKING,
                RobotMode.LANDING,
                RobotMode.ERROR,
                RobotMode.EMERGENCY_STOP,
            ],
            RobotMode.LANDING: [RobotMode.IDLE, RobotMode.ERROR, RobotMode.EMERGENCY_STOP],
            RobotMode.ERROR: [RobotMode.IDLE, RobotMode.EMERGENCY_STOP],
            RobotMode.EMERGENCY_STOP: [RobotMode.IDLE, RobotMode.ERROR],
        }

        return to_mode in valid_transitions.get(from_mode, [])

    def register_mode_change_callback(self, callback: Callable):
        """Регистрирует callback для изменения режима.

        Args:
            callback: Функция, вызываемая при изменении режима
                     Сигнатура: callback(from_mode: RobotMode, to_mode: RobotMode)
        """
        self.on_mode_change_callbacks.append(callback)

    def can_transition_to(self, mode: RobotMode) -> bool:
        """Проверяет возможность перехода в режим.

        Args:
            mode: Целевой режим

        Returns:
            True если переход возможен
        """
        return self._is_valid_transition(self.current_mode, mode)

    def get_mode(self) -> RobotMode:
        """Возвращает текущий режим.

        Returns:
            Текущий режим
        """
        return self.current_mode

    def reset_to_idle(self):
        """Сбрасывает в режим IDLE."""
        if self.can_transition_to(RobotMode.IDLE):
            self.transition_to(RobotMode.IDLE)
