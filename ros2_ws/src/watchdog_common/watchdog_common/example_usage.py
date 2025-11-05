"""Примеры использования watchdog_common."""

import rclpy
from rclpy.node import Node
from watchdog_common.logging import get_logger
from watchdog_common.diagnostics import DiagnosticPublisher, HealthMonitor, HealthStatus
from watchdog_common.config_validator import ConfigValidator


class ExampleNode(Node):
    """Пример узла с улучшенным логированием и диагностикой."""

    def __init__(self):
        super().__init__('example_node')

        # Использование структурированного логирования
        self.logger = get_logger('ExampleNode', node=self)
        self.logger.set_context(node_id='example_001', version='1.0.0')

        # Инициализация диагностики
        self.diag = DiagnosticPublisher(self, hardware_id='watchdog_robot')
        self.lidar_monitor = self.diag.register_monitor('lidar', timeout=5.0)
        self.camera_monitor = self.diag.register_monitor('camera', timeout=3.0)

        self.logger.info('Node initialized', status='starting')

        # Пример обновления мониторов
        self.create_timer(1.0, self.update_health)

    def update_health(self):
        """Обновляет статус здоровья."""
        # Лидар работает нормально
        self.lidar_monitor.update(
            HealthStatus.OK,
            'Lidar scanning normally',
            scan_rate=10.0,
            points_per_scan=360,
        )

        # Камера с предупреждением
        self.camera_monitor.update(
            HealthStatus.WARN,
            'Camera frame rate below expected',
            fps=15.0,
            expected_fps=30.0,
        )

        self.logger.info('Health updated', lidar='OK', camera='WARN')


def example_config_validation():
    """Пример валидации конфигурации."""
    from watchdog_common.config_validator import ConfigValidator

    config = {
        'lidar': {
            'device': '/dev/ttyUSB0',
            'baudrate': 115200,
            'frame_id': 'lidar_frame',
        },
        'camera': {
            'device_id': 0,
            'width': 1920,
            'height': 1080,
            'fps': 30,
        },
        'stm32': {
            'port': '/dev/ttyACM0',
            'baudrate': 115200,
        },
    }

    validator = ConfigValidator()
    try:
        validator.validate(config)
        print('Конфигурация валидна!')
    except Exception as e:
        print(f'Ошибка валидации: {e}')


if __name__ == '__main__':
    example_config_validation()

