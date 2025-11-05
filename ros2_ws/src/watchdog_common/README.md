# watchdog_common

Общие утилиты для всех пакетов WatchDog Robot.

## Компоненты

### Логирование (logging.py)

Структурированное логирование с поддержкой контекста.

```python
from watchdog_common.logging import get_logger

logger = get_logger('MyNode', node=self)
logger.set_context(component='lidar', version='1.0')
logger.info('Lidar initialized', port='/dev/ttyUSB0', baudrate=115200)
```

### Диагностика (diagnostics.py)

Мониторинг здоровья компонентов и публикация диагностической информации.

```python
from watchdog_common.diagnostics import DiagnosticPublisher, HealthMonitor, HealthStatus

# В узле
diag = DiagnosticPublisher(self, hardware_id='watchdog_robot')
lidar_monitor = diag.register_monitor('lidar', timeout=5.0)

# Обновление статуса
lidar_monitor.update(
    HealthStatus.OK,
    'Lidar scanning normally',
    scan_rate=10.0,
    points_per_scan=360
)
```

Диагностика публикуется в топик `/diagnostics` в формате `diagnostic_msgs/DiagnosticArray`.

### Валидация конфигурации (config_validator.py)

Валидация YAML конфигурационных файлов с поддержкой переменных окружения.

```python
from watchdog_common.config_validator import ConfigValidator

# Загрузка и валидация
config = ConfigValidator.load_and_validate('config/robot_config.yaml')

# Или валидация словаря
validator = ConfigValidator()
validator.validate(config_dict)
```

Поддержка переменных окружения:
```yaml
lidar:
  device: ${LIDAR_DEVICE:/dev/ttyUSB0}
  baudrate: ${LIDAR_BAUDRATE:115200}
```

## Использование

Добавьте зависимость в `package.xml`:
```xml
<depend>watchdog_common</depend>
```

Или в `setup.py`:
```python
install_requires=['watchdog_common'],
```

## Установка диагностических сообщений

Для использования диагностики необходимо установить:
```bash
sudo apt install ros-humble-diagnostic-msgs
```

