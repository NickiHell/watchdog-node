# Примеры использования WatchDog Robot

## Запуск системы

### Базовый запуск

```bash
# Запуск всех узлов
ros2 launch watchdog_controller default.launch.py

# Только навигация
ros2 launch watchdog_controller navigation_full.launch.py

# Только интерфейс STM32
ros2 launch watchdog_stm32_interface stm32_interface.launch.py
```

### С Docker

```bash
# Сборка образа
docker build -t watchdog-robot .

# Запуск
docker-compose up

# Разработка
docker build -f Dockerfile.dev -t watchdog-dev .
docker run -it --privileged --network host watchdog-dev
```

## Использование логирования

```python
from watchdog_common.logging import get_logger

class MyNode(Node):
    def __init__(self):
        super().__init__('my_node')
        self.logger = get_logger('MyNode', node=self)
        
        # Установка контекста
        self.logger.set_context(component='lidar', version='1.0')
        
        # Логирование с контекстом
        self.logger.info('Initializing', port='/dev/ttyUSB0')
        self.logger.warn('Low battery', level=45)
```

## Использование диагностики

```python
from watchdog_common.diagnostics import (
    DiagnosticPublisher,
    HealthMonitor,
    HealthStatus
)

class LidarNode(Node):
    def __init__(self):
        super().__init__('lidar_node')
        
        # Инициализация диагностики
        self.diag = DiagnosticPublisher(self)
        self.lidar_monitor = self.diag.register_monitor('lidar', timeout=5.0)
        
    def update_status(self):
        if self.lidar.is_connected:
            self.lidar_monitor.update(
                HealthStatus.OK,
                'Lidar scanning normally',
                scan_rate=10.0,
                points=360
            )
        else:
            self.lidar_monitor.update(
                HealthStatus.ERROR,
                'Lidar disconnected'
            )
```

## Валидация конфигурации

```python
from watchdog_common.config_validator import ConfigValidator

# Загрузка и валидация
try:
    config = ConfigValidator.load_and_validate('config/robot_config.yaml')
    print('Configuration valid!')
except ConfigValidationError as e:
    print(f'Validation error: {e}')
```

## Использование State Machine

```python
from watchdog_controller.state_machine import StateMachine, RobotMode

# Создание state machine
sm = StateMachine(initial_mode=RobotMode.IDLE)

# Переход в режим навигации
if sm.can_transition_to(RobotMode.NAVIGATION):
    sm.transition_to(RobotMode.NAVIGATION)

# Регистрация callback
def on_mode_change(from_mode, to_mode):
    print(f'Mode changed: {from_mode.value} -> {to_mode.value}')

sm.register_mode_change_callback(on_mode_change)
```

## Отправка команд движения

```python
from geometry_msgs.msg import Twist

# Публикация команды движения
cmd = Twist()
cmd.linear.x = 0.5  # м/с
cmd.angular.z = 0.3  # рад/с

cmd_vel_pub.publish(cmd)
```

## Работа с протоколом STM32

```python
from watchdog_stm32_interface.protocol import STM32Protocol

# Кодирование команды движения
packet = STM32Protocol.encode_movement_command(linear_x=0.5, angular_z=0.3)

# Декодирование ответа
try:
    response = STM32Protocol.decode_response(data)
    if response['type'] == ResponseType.ENCODER_DATA:
        left = response['parsed_data']['encoder_left']
        right = response['parsed_data']['encoder_right']
except ProtocolError as e:
    print(f'Protocol error: {e}')
```

## Запуск тестов

```bash
# Все тесты
pytest ros2_ws/src/

# С покрытием
pytest ros2_ws/src/ --cov=ros2_ws/src --cov-report=html

# Конкретный пакет
pytest ros2_ws/src/watchdog_stm32_interface/test/

# Конкретный тест
pytest ros2_ws/src/watchdog_stm32_interface/test/test_protocol.py::TestSTM32Protocol::test_encode_movement_command
```

## Мониторинг системы

```bash
# Просмотр диагностики
ros2 topic echo /diagnostics

# Статус контроллера
ros2 topic echo /controller/state

# Общий статус робота
ros2 topic echo /robot/status

# Список всех топиков
ros2 topic list

# Информация о топике
ros2 topic info /sensor/lidar/scan
```

## Отладка

```bash
# Включить debug логирование
export RCUTILS_LOGGING_SEVERITY=DEBUG

# Запустить узел с подробными логами
ros2 run watchdog_lidar lidar_node --ros-args --log-level debug

# Просмотр логов конкретного узла
ros2 node info /lidar_node
```

