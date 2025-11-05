# WatchDog Robot - ROS2 Mobile Robot Project

Проект колесного/гусеничного робота на базе ROS2 и STM32 с функциями навигации, распознавания лиц и голосового взаимодействия.

## Функционал

1. **Навигация через лидар** - Ориентация в пространстве с использованием лидара от Xiaomi MOP3
2. **Камера 360°** - Распознавание человеческих лиц и отслеживание людей
3. **Голосовое взаимодействие** - Синтез речи и распознавание речи для общения с человеком
4. **Навигация и построение карты** - SLAM на основе лидара, планирование пути к цели
5. **Idle режим** - Наблюдение за людьми через камеру в режиме ожидания

## Рекомендуемые компоненты

### Основной компьютер (ROS2)

**Вариант 1 (Рекомендуемый - лучшая производительность):**
- Beelink Mini PC (Intel N100/N95 или аналогичный) ✅
- Минимум 8GB RAM, рекомендуется 16GB
- SSD 128GB+ (обычно уже установлен)
- Источник питания 12V или 19V (в зависимости от модели)

**Вариант 2 (Бюджетный):**
- Raspberry Pi 4B (4GB RAM) или 4GB+
- MicroSD 64GB+ (Class 10)
- Источник питания 5V 3A

**Вариант 3 (Альтернативы):**
- Raspberry Pi 5 (8GB RAM) или
- NVIDIA Jetson Nano (4GB) или
- Intel NUC (i3/i5)
- SSD 128GB+ для лучшей производительности

### Контроллер движения (STM32)

**Вариант 1 (Рекомендуемый):**
- STM32F407VGT6 (Cortex-M4, 168MHz, 1MB Flash, 192KB RAM)
- STM32 Discovery Board или Nucleo-F407ZG

**Вариант 2 (Совместимо):**
- STM32F411RE (Cortex-M4, 100MHz, 512KB Flash, 128KB RAM)
- NUCLEO-F411RE (✅ Поддерживается)

**Вариант 3 (Более мощный):**
- STM32H743VIT6 (Cortex-M7, 480MHz, 2MB Flash, 1MB RAM)
- STM32 Nucleo-H743ZI2

**Драйверы моторов:**
- DRV8833 или L298N (для колесных роботов)
- BTS7960 (для более мощных моторов)
- Два мотора с энкодерами (например, Pololu 37D Metal Gearmotor)

### Лидар

**Рекомендуемые варианты:**
- **RPLidar A1/A2/A3** - Полная поддержка, хорошо документирован
- **RPLiDAR ToF C1** - ⚠️ Требует проверки совместимости (см. `docs/RPLIDAR_TOF_C1_SETUP.md`)
- **Xiaomi MOP3 LiDAR** - Требует generic режим или реверс-инжиниринг

**Дополнительно:**
- USB-UART конвертер для подключения к Raspberry Pi (CP2102 или CH340)
- Источник питания 5V для лидара

### Камера 360°

**Вариант 1:**
- Insta360 ONE X2 или аналогичная
- Подключение через USB-C

**Вариант 2 (Бюджетный):**
- Несколько веб-камер (2-4 шт) с широким углом обзора
- USB-хаб для подключения

**Вариант 3 (Для распознавания лиц):**
- Raspberry Pi Camera Module v3 (широкоугольная)
- USB веб-камера с автофокусом (например, Logitech C920/C930)


### Аудио система

- Микрофон: USB микрофон или MEMS микрофон с ADC (для STM32)
- Динамик: USB звуковая карта с выходом на динамик или встроенный в Raspberry Pi аудио выход
- Аудио усилитель (опционально): PAM8403 или аналогичный

### Питание

- Аккумулятор Li-Po 12V 5000mAh+ (для моторов)
- Step-down преобразователь 12V → 5V (для Raspberry Pi и периферии)
- Step-down преобразователь 12V → 3.3V (для STM32)
- Зарядное устройство Li-Po

### Дополнительно

- Шасси колесное/гусеничное (например, DFRobot Devastator или кастомное)
- IMU датчик (MPU6050 или MPU9250) - опционально, для дополнения навигации
- Датчики столкновения (bump sensors) - опционально

## Схема подключения

```
┌─────────────────────────────────────────────────────────────┐
│                    Raspberry Pi 5 (ROS2)                      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Камера 360 │  │    Лидар     │  │   Микрофон    │   │
│  │     USB      │  │  USB-UART    │  │     USB       │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          UART / I2C / SPI → STM32                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │   Динамик    │  │   Bluetooth  │                          │
│  │  USB Audio   │  │   (Маяк)     │                          │
│  └──────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ UART/I2C/SPI
                         │
┌─────────────────────────────────────────────────────────────┐
│                    STM32F407 (Контроллер)                    │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │  Драйвер     │  │  Драйвер     │  │    Энкодеры  │   │
│  │   Мотор 1    │  │   Мотор 2    │  │   (GPIO/ADC) │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │    IMU       │  │  Bump sensors│                          │
│  │  (I2C/SPI)   │  │   (GPIO)     │                          │
│  └──────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
                         │
                         │
                    ┌─────────┐
                    │ Li-Po   │
                    │ 12V     │
                    └─────────┘
```

### Детали подключения

#### STM32 ↔ Raspberry Pi

**Вариант 1 (UART - Рекомендуемый):**
```
Raspberry Pi          STM32
─────────────────────────────
GPIO 14 (TX)    →     PA10 (RX)
GPIO 15 (RX)    →     PA9 (TX)
GND             →     GND
```

**Вариант 2 (I2C):**
```
Raspberry Pi          STM32
─────────────────────────────
GPIO 2 (SDA)    →     PB7 (SDA)
GPIO 3 (SCL)    →     PB6 (SCL)
GND             →     GND
```

**Вариант 3 (SPI):**
```
Raspberry Pi          STM32
─────────────────────────────
GPIO 10 (MOSI)  →     PA7 (MOSI)
GPIO 9 (MISO)   →     PA6 (MISO)
GPIO 11 (SCLK)  →     PA5 (SCK)
GPIO 8 (CE0)    →     PA4 (NSS)
GND             →     GND
```

#### Драйверы моторов → STM32

```
Драйвер 1 (Мотор левый):
┌─────────────────┐
│ IN1 → STM32 PA0 │
│ IN2 → STM32 PA1 │
│ EN  → STM32 PA2 (PWM) │
│ Motor + → Мотор 1 │
│ Motor - → Мотор 1 │
└─────────────────┘

Драйвер 2 (Мотор правый):
┌─────────────────┐
│ IN1 → STM32 PA3 │
│ IN2 → STM32 PA4 │
│ EN  → STM32 PA5 (PWM) │
│ Motor + → Мотор 2 │
│ Motor - → Мотор 2 │
└─────────────────┘
```

#### Энкодеры → STM32

```
Энкодер Мотор 1:
┌─────────────────┐
│ Channel A → STM32 PB6 (TIM4_CH1) │
│ Channel B → STM32 PB7 (TIM4_CH2) │
│ VCC → 3.3V │
│ GND → GND │
└─────────────────┘

Энкодер Мотор 2:
┌─────────────────┐
│ Channel A → STM32 PB8 (TIM4_CH3) │
│ Channel B → STM32 PB9 (TIM4_CH4) │
│ VCC → 3.3V │
│ GND → GND │
└─────────────────┘
```

#### Лидар MOP3 → Raspberry Pi

```
Лидар MOP3:
┌─────────────────┐
│ TX → USB-UART RX │
│ RX → USB-UART TX │
│ GND → USB-UART GND │
│ VCC → 5V (через USB-UART или внешний) │
└─────────────────┘

USB-UART (например, CP2102/CH340) → Raspberry Pi USB
```

## Структура проекта

```
watchdog-node/
├── ros2_ws/
│   └── src/
│       ├── watchdog_lidar/          # Драйвер лидара MOP3
│       ├── watchdog_camera/          # Обработка камеры 360°
│       ├── watchdog_face_detection/  # Распознавание лиц
│       ├── watchdog_speech/           # Синтез и распознавание речи
│       ├── watchdog_navigation/       # Навигация и планирование пути
│       └── watchdog_controller/      # Главный контроллер (координация)
├── stm32_firmware/                   # Прошивка STM32
│   ├── src/
│   ├── include/
│   └── STM32CubeIDE/
├── config/                           # Конфигурационные файлы
├── docs/                             # Документация
└── README.md
```

## Установка и настройка

### Требования

- Ubuntu 22.04 или Ubuntu 24.04
- ROS2 Humble или ROS2 Iron
- Python 3.11+
- STM32CubeIDE (для разработки прошивки)
- CMake 3.8+

### Установка ROS2

```bash
# Для Ubuntu 22.04 (ROS2 Humble)
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/ros2-latest.list'
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions -y
```

### Сборка проекта

```bash
cd ~/Workspace/Projects/nickihell/watchdog-node
source /opt/ros/humble/setup.bash
cd ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Архитектура (SOLID принципы)

Проект организован по принципам SOLID:

- **Single Responsibility** - Каждый пакет отвечает за одну функцию
- **Open/Closed** - Расширяемость через интерфейсы
- **Liskov Substitution** - Интерфейсы для датчиков и актуаторов
- **Interface Segregation** - Малые, специализированные интерфейсы
- **Dependency Inversion** - Зависимости через ROS2 topics/services

### Основные ROS2 топики

```
/sensor/lidar/scan              # Лидар данные (sensor_msgs/LaserScan)
/camera/image_raw                # Изображение камеры (sensor_msgs/Image)
/face_detection/detections       # Обнаруженные лица (custom_msgs/FaceDetections)
/speech/recognized_text          # Распознанный текст (std_msgs/String)
/speech/synthesis_request        # Запрос синтеза речи (std_msgs/String)
/navigation/cmd_vel              # Команды движения (geometry_msgs/Twist)
/controller/state                # Состояние контроллера (custom_msgs/ControllerState)
```

## 🔌 Протокол связи STM32 ↔ ROS2

### Формат сообщений (UART)

```
Заголовок (2 байта): [0xAA, 0x55]
Тип команды (1 байт):
  - 0x01: Команда движения (cmd_vel)
  - 0x02: Запрос состояния
  - 0x03: Установка параметров
Данные (N байт): Зависит от типа команды
Контрольная сумма (1 байт): XOR всех байт
```

### Команда движения (0x01)

```
Байт 0: Тип команды (0x01)
Байт 1-4: linear.x (float, 32-bit)
Байт 5-8: angular.z (float, 32-bit)
Байт 9: Контрольная сумма
```

### Ответ от STM32

```
Байт 0-1: Заголовок [0xAA, 0x55]
Байт 2: Тип ответа:
  - 0x10: Ошибка
  - 0x11: Успех
  - 0x12: Данные энкодеров
Байт 3-N: Данные
Байт N+1: Контрольная сумма
```

## Разработка

### Создание нового пакета

```bash
cd ros2_ws/src
ros2 pkg create --build-type ament_python watchdog_<package_name> --dependencies rclpy std_msgs sensor_msgs
```

### Тестирование

```bash
# Запуск всех тестов
colcon test

# Просмотр результатов
colcon test-result --verbose
```

## Документация

Детальная документация по каждому модулю находится в папке `docs/`.

**Важные документы:**
- `SELECTED_COMPONENTS_SUMMARY.md` - ✅ Итоговый список выбранных компонентов
- `HARDWARE_SELECTED.md` - Полный список выбранных компонентов с деталями
- `CHASSIS_DESIGN_GUIDE.md` - 📐 Руководство по проектированию шасси и корпуса
- `HARDWARE_COMPATIBILITY.md` - Анализ совместимости и недостающие компоненты
- `docs/BEELINK_MINI_PC_SETUP.md` - Настройка Beelink Mini PC
- `docs/RPLIDAR_TOF_C1_SETUP.md` - Настройка RPLiDAR ToF C1
- `docs/HARDWARE_RECOMMENDATIONS.md` - Рекомендации по выбору компонентов
- `stm32_firmware/STM32CubeMX_Configuration.md` - Конфигурация STM32 (включая F411RE)

## Автор

NickiHell
