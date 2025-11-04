"""Диагностика и мониторинг здоровья для WatchDog."""

import time
from typing import Dict, Optional, Callable
from enum import Enum
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

try:
    from diagnostic_msgs.msg import DiagnosticStatus, DiagnosticArray, KeyValue
    DIAGNOSTIC_MSGS_AVAILABLE = True
except ImportError:
    DIAGNOSTIC_MSGS_AVAILABLE = False
    DiagnosticStatus = None
    DiagnosticArray = None
    KeyValue = None


class HealthStatus(Enum):
    """Статус здоровья компонента."""

    OK = 0  # Все хорошо
    WARN = 1  # Предупреждение
    ERROR = 2  # Ошибка
    STALE = 3  # Данные устарели


class HealthMonitor:
    """Монитор здоровья компонента."""

    def __init__(self, name: str, timeout: float = 5.0):
        """Инициализирует монитор здоровья.

        Args:
            name: Имя компонента
            timeout: Таймаут в секундах для определения устаревших данных
        """
        self.name = name
        self.timeout = timeout
        self.last_update_time: Optional[float] = None
        self.status = HealthStatus.OK
        self.message = ''
        self.values: Dict[str, str] = {}

    def update(self, status: HealthStatus = HealthStatus.OK, message: str = '', **values):
        """Обновляет статус здоровья.

        Args:
            status: Статус здоровья
            message: Сообщение о статусе
            **values: Дополнительные значения для диагностики
        """
        self.last_update_time = time.time()
        self.status = status
        self.message = message
        self.values.update({k: str(v) for k, v in values.items()})

    def get_status(self) -> HealthStatus:
        """Возвращает текущий статус здоровья.

        Returns:
            Статус здоровья
        """
        if self.last_update_time is None:
            return HealthStatus.STALE

        elapsed = time.time() - self.last_update_time
        if elapsed > self.timeout:
            return HealthStatus.STALE

        return self.status

    def is_healthy(self) -> bool:
        """Проверяет, здоров ли компонент.

        Returns:
            True если компонент здоров
        """
        return self.get_status() == HealthStatus.OK


class DiagnosticPublisher:
    """Публикатор диагностической информации."""

    def __init__(self, node: Node, hardware_id: str = 'watchdog_robot'):
        """Инициализирует публикатор диагностики.

        Args:
            node: ROS2 узел
            hardware_id: ID оборудования
        """
        if not DIAGNOSTIC_MSGS_AVAILABLE:
            raise ImportError('diagnostic_msgs не доступен. Установите: sudo apt install ros-humble-diagnostic-msgs')

        self.node = node
        self.hardware_id = hardware_id
        self.monitors: Dict[str, HealthMonitor] = {}

        qos = QoSProfile(
            depth=10,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

        self.diag_pub = node.create_publisher(DiagnosticArray, '/diagnostics', qos)
        self.publish_timer = node.create_timer(1.0, self.publish_diagnostics)

    def register_monitor(self, name: str, timeout: float = 5.0) -> HealthMonitor:
        """Регистрирует монитор здоровья.

        Args:
            name: Имя компонента
            timeout: Таймаут для определения устаревших данных

        Returns:
            HealthMonitor экземпляр
        """
        monitor = HealthMonitor(name, timeout)
        self.monitors[name] = monitor
        return monitor

    def publish_diagnostics(self):
        """Публикует диагностическую информацию."""
        if not DIAGNOSTIC_MSGS_AVAILABLE:
            return

        diag_array = DiagnosticArray()
        diag_array.header.stamp = self.node.get_clock().now().to_msg()
        diag_array.header.frame_id = self.hardware_id

        for name, monitor in self.monitors.items():
            status = DiagnosticStatus()
            status.name = name
            status.hardware_id = self.hardware_id

            health_status = monitor.get_status()

            # Маппинг HealthStatus в DiagnosticStatus.level
            if health_status == HealthStatus.OK:
                status.level = DiagnosticStatus.OK
                status.message = monitor.message or 'OK'
            elif health_status == HealthStatus.WARN:
                status.level = DiagnosticStatus.WARN
                status.message = monitor.message or 'Warning'
            elif health_status == HealthStatus.ERROR:
                status.level = DiagnosticStatus.ERROR
                status.message = monitor.message or 'Error'
            else:  # STALE
                status.level = DiagnosticStatus.STALE
                status.message = f'Data stale (timeout: {monitor.timeout}s)'

            # Добавляем значения
            for key, value in monitor.values.items():
                kv = KeyValue()
                kv.key = key
                kv.value = value
                status.values.append(kv)

            # Добавляем метаданные
            if monitor.last_update_time:
                elapsed = time.time() - monitor.last_update_time
                kv_elapsed = KeyValue()
                kv_elapsed.key = 'time_since_update'
                kv_elapsed.value = f'{elapsed:.2f}s'
                status.values.append(kv_elapsed)

            diag_array.status.append(status)

        self.diag_pub.publish(diag_array)

