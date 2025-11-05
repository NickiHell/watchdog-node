# Настройка Beelink Mini PC для WatchDog Robot

Beelink Mini PC - отличный выбор для WatchDog Robot! Он значительно мощнее Raspberry Pi и лучше справляется с ROS2, SLAM и обработкой видео.

## Преимущества Beelink Mini PC

### Производительность
- **x86 архитектура** (Intel N100/N95 или аналогичный) - значительно быстрее ARM
- **Больше RAM** - обычно 8-16GB (vs 4-8GB у Raspberry Pi)
- **SSD накопитель** - намного быстрее чем MicroSD
- **Больше USB портов** - удобно для подключения всех устройств
- **Лучше для ML** - быстрее обработка моделей распознавания лиц

### Сравнение с Raspberry Pi

| Параметр | Raspberry Pi 5 | Beelink Mini PC |
|----------|----------------|-----------------|
| Процессор | ARM Cortex-A76 (4 ядра) | Intel x86 (4-8 ядер) |
| RAM | 4-8GB | 8-16GB |
| Хранилище | MicroSD (медленно) | SSD (быстро) |
| Производительность | Хорошая | **Отличная** |
| Стоимость | ~$80 | ~$100-200 |
| Питание | 5V 3A | 12V/19V (зависит от модели) |

## Настройка

### Шаг 1: Установка Ubuntu

Beelink Mini PC обычно поставляется с Windows. Установите Ubuntu 22.04 или 24.04:

1. Скачайте Ubuntu 22.04 Desktop ISO
2. Создайте загрузочную USB флешку
3. Загрузитесь с USB и установите Ubuntu
4. При установке выберите "Erase disk and install Ubuntu" (или создайте раздел)

### Шаг 2: Установка ROS2

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка ROS2 Humble (для Ubuntu 22.04)
sudo apt install software-properties-common -y
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions -y

# Или для Ubuntu 24.04 (ROS2 Iron)
# sudo apt install ros-iron-desktop python3-colcon-common-extensions -y
```

### Шаг 3: Настройка проекта

```bash
# Клонирование или копирование проекта
cd ~/Workspace/Projects/nickihell/watchdog-node

# Сборка проекта
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

### Шаг 4: Проверка USB портов

Beelink Mini PC обычно имеет много USB портов, но проверьте:

```bash
# Проверка USB устройств
lsusb

# Проверка последовательных портов
ls -l /dev/ttyUSB* /dev/ttyACM*
```

Подключите:
- Камеру (USB)
- Лидар через USB-UART адаптер (CP2102/CH340)
- Микрофон (USB)
- USB-UART для связи с STM32 (если используете USB-UART)

## Питание

### Важно: Проверьте напряжение питания вашей модели

Beelink Mini PC обычно питается от:
- **12V** (многие модели)
- **19V** (некоторые модели)

**Проверьте на блоке питания или в документации!**

### Подключение к аккумулятору робота

Если Beelink Mini PC питается от **12V**:
```
Аккумулятор 12V → Beelink Mini PC (напрямую, если есть подходящий разъем)
                → Преобразователь 12V→3.3V → STM32
```

Если Beelink Mini PC питается от **19V**:
```
Аккумулятор 12V → Step-up преобразователь 12V→19V → Beelink Mini PC
                → Преобразователь 12V→3.3V → STM32
```

**Рекомендация:** Используйте преобразователь с защитой от переполюсовки и стабилизацией напряжения.

### Расчет потребления

Beelink Mini PC обычно потребляет:
- **10-30W** (зависит от нагрузки)
- При 12V: **0.8-2.5A**
- При 19V: **0.5-1.6A**

Убедитесь, что аккумулятор достаточной емкости для работы 1-2 часа.

## Подключение STM32

### Вариант 1: Прямое UART подключение

Если Beelink Mini PC имеет UART порт (редко):
```
STM32 PA9 (TX) → Beelink UART RX
STM32 PA10 (RX) → Beelink UART TX
GND → GND
```

### Вариант 2: USB-UART адаптер (рекомендуется)

Используйте USB-UART адаптер (CP2102, CH340, FT232):
```
STM32 PA9 (TX) → USB-UART RX
STM32 PA10 (RX) → USB-UART TX
GND → GND

USB-UART → Beelink Mini PC USB порт
```

Настройте права доступа:
```bash
sudo usermod -a -G dialout $USER
# Перелогиньтесь
```

## Производительность

### Оптимизация для Beelink Mini PC

Beelink Mini PC достаточно мощный, но можно оптимизировать:

1. **Отключите неиспользуемые сервисы:**
```bash
sudo systemctl disable bluetooth
sudo systemctl disable snapd
```

2. **Используйте SSD** (обычно уже установлен, но проверьте)

3. **Настройте приоритет процессов:**
```bash
# Для ROS2 узлов можно установить высокий приоритет
nice -n -10 ros2 run watchdog_lidar lidar_node
```

4. **Мониторинг производительности:**
```bash
# Установка инструментов мониторинга
sudo apt install htop -y

# Запуск мониторинга
htop
```

## Тестирование

### Проверка работы всех компонентов

```bash
# Терминал 1: Лидар
ros2 run watchdog_lidar lidar_node

# Терминал 2: Камера
ros2 run watchdog_camera camera_node

# Терминал 3: STM32 интерфейс
ros2 run watchdog_stm32_interface stm32_interface_node

# Терминал 4: Проверка данных
ros2 topic list
ros2 topic echo /sensor/lidar/scan
ros2 topic echo /camera/image_raw
```

### Проверка производительности

```bash
# Мониторинг CPU и памяти
htop

# Проверка загрузки ROS2
ros2 topic hz /sensor/lidar/scan
ros2 topic hz /camera/image_raw
```

## Решение проблем

### Проблема: "Недостаточно USB портов"

**Решение:**
- Используйте USB-хаб (с внешним питанием)
- Или используйте встроенные USB порты для критичных устройств

### Проблема: "Высокое потребление энергии"

**Решение:**
- Отключите неиспользуемые USB устройства
- Настройте энергосбережение:
```bash
# Установка powertop
sudo apt install powertop -y

# Оптимизация
sudo powertop --auto-tune
```

### Проблема: "Перегрев"

**Решение:**
- Убедитесь в хорошей вентиляции
- Проверьте температуру:
```bash
sensors
```

### Проблема: "Не работает USB-UART"

**Решение:**
```bash
# Проверка прав доступа
ls -l /dev/ttyUSB*

# Добавление в группу
sudo usermod -a -G dialout $USER
# Перелогиньтесь

# Временное решение
sudo chmod 666 /dev/ttyUSB0
```

## Преимущества для WatchDog Robot

1. **Быстрее SLAM** - x86 процессор быстрее обрабатывает данные лидара
2. **Быстрее распознавание лиц** - больше RAM для ML моделей
3. **Быстрее обработка видео** - больше вычислительной мощности
4. **Меньше задержек** - SSD быстрее MicroSD
5. **Лучше для отладки** - можно использовать полноценный IDE, браузер и т.д.

## Итого

Beelink Mini PC - отличный выбор для WatchDog Robot! Он обеспечит:
- ✅ Высокую производительность ROS2
- ✅ Быструю обработку SLAM
- ✅ Эффективное распознавание лиц
- ✅ Стабильную работу всех узлов

Единственное отличие от Raspberry Pi - нужно правильно настроить питание в зависимости от модели Beelink Mini PC.

