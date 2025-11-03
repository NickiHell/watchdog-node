# Архитектура проекта WatchDog Robot

## Принципы проектирования

Проект построен на основе принципов SOLID и лучших практик ROS2:

### Single Responsibility Principle (SRP)
Каждый пакет отвечает за одну конкретную задачу:
- `watchdog_lidar` - только работа с лидаром
- `watchdog_camera` - только захват изображений
- `watchdog_face_detection` - только распознавание лиц
- `watchdog_speech` - только обработка речи
- `watchdog_navigation` - только навигация
- `watchdog_beacon` - только отслеживание маяка
- `watchdog_controller` - координация всех модулей

### Open/Closed Principle (OCP)
Модули расширяются через:
- ROS2 интерфейсы (topics/services)
- Параметризация через конфигурационные файлы
- Возможность замены реализаций без изменения кода

### Liskov Substitution Principle (LSP)
Используются стандартные ROS2 типы сообщений, что обеспечивает совместимость:
- `sensor_msgs/LaserScan` для лидара
- `sensor_msgs/Image` для камеры
- `geometry_msgs/Twist` для движения
- `geometry_msgs/PoseStamped` для позиций

### Interface Segregation Principle (ISP)
Маленькие, специализированные интерфейсы:
- Отдельные топики для каждого типа данных
- Специфичные сервисы для каждой операции

### Dependency Inversion Principle (DIP)
Зависимости через абстракции:
- Все модули общаются через ROS2 топики
- Нет прямых зависимостей между модулями
- Контроллер зависит от интерфейсов, а не реализаций

## Архитектура системы

```
┌─────────────────────────────────────────────────────────┐
│                  WatchDog Controller                      │
│  (Координатор всех подсистем)                            │
└─────────────────────────────────────────────────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Lidar     │ │   Camera    │ │    Speech   │ │  Navigation │
│   Driver    │ │   Capture   │ │  Processing │ │   Planner   │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  MOP3       │ │  360° Cam    │ │  TTS/STT    │ │  Beacon     │
│  LiDAR      │ │   Hardware   │ │  Models     │ │  Tracker    │
└─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                                                    │
                                                    ▼
                                           ┌─────────────────┐
                                           │   STM32 Firmware│
                                           │  Motor Control   │
                                           └─────────────────┘
```

## Поток данных

### Режим Idle (наблюдение)
```
Camera → Face Detection → Controller → (если лица найдены)
                                        → Speech Synthesis
                                        → Camera Tracking
```

### Режим Навигации
```
Lidar → Navigation → Controller → STM32 → Motors
                      ↓
                  Beacon (позиция)
```

### Режим Отслеживания маяка
```
Beacon → Controller → Navigation → STM32 → Motors
                           ↓
                        Lidar (препятствия)
```

## ROS2 Топики и сервисы

### Сенсоры
- `/sensor/lidar/scan` (sensor_msgs/LaserScan) - данные лидара
- `/camera/image_raw` (sensor_msgs/Image) - изображение камеры
- `/beacon/position` (geometry_msgs/PoseStamped) - позиция маяка

### Обработка
- `/face_detection/detections` (custom_msgs/FaceDetections) - обнаруженные лица
- `/speech/recognized_text` (std_msgs/String) - распознанный текст
- `/speech/synthesis_request` (std_msgs/String) - запрос синтеза

### Управление
- `/cmd_vel` (geometry_msgs/Twist) - команды движения
- `/controller/state` (custom_msgs/ControllerState) - состояние системы
- `/navigation/goal` (geometry_msgs/PoseStamped) - целевая точка

### Параметры
Все параметры настраиваются через `config/robot_config.yaml`

## Коммуникация STM32 ↔ ROS2

Протокол через UART/I2C/SPI:
- Команды движения: `geometry_msgs/Twist` → бинарный протокол
- Состояние: данные энкодеров → `nav_msgs/Odometry`
- Ошибки и статус: текстовые сообщения

## Расширяемость

Система легко расширяется:
1. Добавление новых датчиков - новый пакет с драйвером
2. Новые алгоритмы - замена узла обработки
3. Дополнительные режимы - расширение контроллера
4. Новые интерфейсы - добавление сервисов/экшенов

## Безопасность и надежность

- Изоляция модулей через ROS2
- Обработка ошибок в каждом узле
- Timeout для связи с STM32
- Проверка валидности данных
- Логирование всех критических операций

