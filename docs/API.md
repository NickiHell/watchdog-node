# API Документация WatchDog Robot

## watchdog_common

### logging

#### `get_logger(name: str, node: Optional[Node] = None) -> StructuredLogger`

Создает структурированный логгер с поддержкой контекста.

**Параметры:**
- `name`: Имя логгера
- `node`: ROS2 узел (опционально)

**Пример:**
```python
from watchdog_common.logging import get_logger

logger = get_logger('LidarNode', node=self)
logger.set_context(component='lidar', port='/dev/ttyUSB0')
logger.info('Lidar initialized', baudrate=115200)
```

#### `StructuredLogger`

Класс структурированного логирования.

**Методы:**
- `set_context(**kwargs)`: Устанавливает контекст
- `clear_context()`: Очищает контекст
- `debug(message, **kwargs)`: Debug сообщение
- `info(message, **kwargs)`: Info сообщение
- `warn(message, **kwargs)`: Warning сообщение
- `error(message, **kwargs)`: Error сообщение
- `fatal(message, **kwargs)`: Fatal сообщение

### diagnostics

#### `DiagnosticPublisher(node: Node, hardware_id: str = 'watchdog_robot')`

Публикатор диагностической информации.

**Параметры:**
- `node`: ROS2 узел
- `hardware_id`: ID оборудования

**Методы:**
- `register_monitor(name: str, timeout: float = 5.0) -> HealthMonitor`: Регистрирует монитор

#### `HealthMonitor(name: str, timeout: float = 5.0)`

Монитор здоровья компонента.

**Методы:**
- `update(status: HealthStatus, message: str = '', **values)`: Обновляет статус
- `get_status() -> HealthStatus`: Возвращает статус
- `is_healthy() -> bool`: Проверяет здоровье

#### `HealthStatus`

Enum статусов здоровья:
- `OK`: Все хорошо
- `WARN`: Предупреждение
- `ERROR`: Ошибка
- `STALE`: Данные устарели

### config_validator

#### `ConfigValidator(schema: Optional[Dict] = None)`

Валидатор конфигурации.

**Методы:**
- `validate(config: Dict) -> bool`: Валидирует конфигурацию
- `load_and_validate(config_path: str, schema: Optional[Dict] = None) -> Dict`: Загружает и валидирует

## watchdog_controller

### `ControllerNode`

Главный контроллер робота.

**Параметры:**
- `default_mode`: Режим по умолчанию ('idle', 'navigation', 'tracking')
- `update_rate`: Частота обновления (Hz)
- `emergency_stop_distance`: Расстояние для аварийной остановки (м)

**Топики:**
- Публикует: `/cmd_vel`, `/controller/state`, `/robot/status`
- Подписывается: `/sensor/lidar/scan`, `/face_detection/detections`, `/navigation/goal`

### `StateMachine`

Конечный автомат для управления режимами.

**Методы:**
- `transition_to(new_mode: RobotMode) -> bool`: Переход в режим
- `can_transition_to(mode: RobotMode) -> bool`: Проверка возможности перехода
- `get_mode() -> RobotMode`: Текущий режим
- `register_mode_change_callback(callback)`: Регистрация callback

### `RobotMode`

Режимы работы:
- `IDLE`: Ожидание
- `NAVIGATION`: Навигация
- `TRACKING`: Отслеживание
- `ERROR`: Ошибка
- `EMERGENCY_STOP`: Аварийная остановка

## watchdog_stm32_interface

### `STM32Protocol`

Протокол связи со STM32.

**Методы:**
- `encode_movement_command(linear_x: float, angular_z: float) -> bytes`: Кодирует команду движения
- `encode_status_request() -> bytes`: Кодирует запрос состояния
- `decode_response(data: bytes) -> dict`: Декодирует ответ
- `calculate_checksum(data: bytes) -> int`: Вычисляет контрольную сумму

## watchdog_lidar

### `LidarDriver` (ABC)

Базовый класс драйвера лидара.

**Методы:**
- `connect() -> bool`: Подключение
- `disconnect()`: Отключение
- `start_scanning() -> bool`: Начать сканирование
- `stop_scanning()`: Остановить сканирование
- `get_scan() -> Optional[LidarScan]`: Получить скан
- `get_info() -> dict`: Информация о лидаре

### `LidarScan`

Структура данных скана.

**Атрибуты:**
- `ranges: List[float]`: Расстояния
- `angles: List[float]`: Углы
- `intensities: List[float]`: Интенсивности
- `timestamp: float`: Временная метка

**Методы:**
- `to_laserscan(frame_id: str) -> LaserScan`: Конвертация в ROS2 сообщение

