# Настройка RPLiDAR ToF C1

Руководство по подключению и настройке RPLiDAR ToF C1 для WatchDog Robot.

## Проверка совместимости

RPLiDAR ToF C1 может использовать другой протокол, чем стандартные RPLidar A1/A2/A3. Следуйте инструкциям ниже для проверки и настройки.

## Шаг 1: Подключение

1. Подключите RPLiDAR ToF C1 через USB к Raspberry Pi
2. Проверьте обнаружение устройства:
   ```bash
   ls -l /dev/ttyUSB* /dev/ttyACM*
   ```
3. Обычно появляется `/dev/ttyUSB0` или `/dev/ttyACM0`

## Шаг 2: Проверка протокола

### Вариант 1: Попробовать стандартный RPLidar драйвер

Сначала попробуйте использовать стандартный драйвер:

```bash
ros2 run watchdog_lidar lidar_node --ros-args \
  -p lidar.type:=rplidar \
  -p lidar.port:=/dev/ttyUSB0 \
  -p lidar.baudrate:=115200
```

**Проверка:**
```bash
# В другом терминале
ros2 topic echo /sensor/lidar/scan
```

Если данные появляются - ToF C1 совместим с протоколом RPLidar! ✅

### Вариант 2: Проверка через generic режим

Если стандартный драйвер не работает, используйте generic режим:

```bash
ros2 run watchdog_lidar lidar_node --ros-args \
  -p lidar.type:=generic \
  -p lidar.port:=/dev/ttyUSB0 \
  -p lidar.baudrate:=115200
```

**Проверка:**
```bash
ros2 topic echo /sensor/lidar/scan
```

Generic драйвер пытается автоматически определить формат данных.

### Вариант 3: Анализ протокола

Если оба варианта не работают, нужно проанализировать протокол:

```python
import serial
import time

# Подключение
ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)

# Чтение данных
data = ser.read(1000)
print(data.hex())

# Сохранение для анализа
with open('lidar_data.bin', 'wb') as f:
    f.write(data)
```

Затем проанализируйте hex дамп:
```bash
hexdump -C lidar_data.bin | head -50
```

## Шаг 3: Настройка конфигурации

### Если работает с rplidar драйвером:

Обновите `ros2_ws/src/watchdog_lidar/config/lidar_config.yaml`:

```yaml
lidar:
  type: "rplidar"
  port: "/dev/ttyUSB0"
  baudrate: 115200  # Проверьте в документации ToF C1
  frame_id: "lidar_frame"
  angle_min: -3.14159
  angle_max: 3.14159
  range_min: 0.05
  range_max: 12.0  # Уточните максимальную дальность для ToF C1
  scan_rate: 10.0
```

### Если работает с generic драйвером:

```yaml
lidar:
  type: "generic"
  port: "/dev/ttyUSB0"
  baudrate: 115200  # Проверьте в документации
  frame_id: "lidar_frame"
  angle_min: -3.14159
  angle_max: 3.14159
  range_min: 0.05
  range_max: 12.0
  scan_rate: 10.0
```

## Шаг 4: Создание специфичного драйвера (если нужно)

Если ни один из вариантов не работает, создайте драйвер для ToF C1:

1. Изучите документацию ToF C1 (если доступна)
2. Проанализируйте протокол через hex дамп
3. Создайте новый драйвер в `ros2_ws/src/watchdog_lidar/watchdog_lidar/tof_c1_driver.py`:

```python
from watchdog_lidar.lidar_base import LidarDriver, LidarScan

class TOFC1Driver(LidarDriver):
    """Драйвер для RPLiDAR ToF C1."""
    
    def __init__(self, port: str, baudrate: int = 115200):
        super().__init__(port, baudrate)
        # Реализуйте методы на основе протокола ToF C1
    
    def connect(self) -> bool:
        # Реализация подключения
        pass
    
    def start_scanning(self) -> bool:
        # Реализация начала сканирования
        pass
    
    def get_scan(self) -> Optional[LidarScan]:
        # Реализация получения скана
        pass
```

4. Добавьте поддержку в `lidar_node.py`:

```python
from watchdog_lidar.tof_c1_driver import TOFC1Driver

# В методе _initialize_lidar
elif lidar_type == 'tof_c1':
    self.lidar = TOFC1Driver(port, baudrate)
```

## Характеристики ToF C1

**Важно:** Уточните характеристики в документации вашего устройства:

- **Дальность:** Обычно 0.05-12 м (уточните)
- **Угол обзора:** 360° (обычно для лидаров)
- **Частота сканирования:** 10-15 Гц (уточните)
- **Скорость передачи:** 115200 или другая (уточните)
- **Протокол:** UART, формат данных (уточните)

## Решение проблем

### Проблема: "Permission denied"

```bash
sudo usermod -a -G dialout $USER
# Перелогиньтесь
```

### Проблема: "Device not found"

1. Проверьте подключение кабеля
2. Проверьте питание лидара
3. Попробуйте другой USB порт
4. Проверьте: `dmesg | tail` для системных сообщений

### Проблема: "Нет данных"

1. Проверьте скорость передачи (baudrate)
2. Попробуйте разные значения: 9600, 115200, 256000
3. Проверьте логи: `ros2 topic echo /lidar/status`
4. Убедитесь, что лидар запущен и вращается

### Проблема: "Неправильные расстояния"

1. Проверьте `range_min` и `range_max` параметры
2. Убедитесь в правильном типе лидара
3. Проверьте масштаб данных (могут быть в мм, см или м)

## Дополнительные ресурсы

- Документация RPLiDAR ToF C1 (если доступна)
- Форум SLAMTEC (производитель RPLidar)
- ROS2 сообщество для помощи с драйверами

## Проверка работы

После настройки:

```bash
# Запустите узел
ros2 run watchdog_lidar lidar_node

# В другом терминале - визуализация
rviz2
# Добавьте LaserScan: Fixed Frame: lidar_frame, Topic: /sensor/lidar/scan
```

Вы должны увидеть данные сканирования в RViz2.

