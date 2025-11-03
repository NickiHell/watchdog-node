# Настройка SLAM и навигации для WatchDog Robot

Подробное руководство по настройке построения карты и навигации на основе лидара.

## Обзор

Система навигации WatchDog использует:
1. **Лидар** - для получения данных об окружении
2. **SLAM (slam_toolbox)** - для построения карты
3. **Планирование пути** - для поиска маршрута к цели
4. **Избежание препятствий** - для безопасного движения

## Установка зависимостей

### SLAM Toolbox

```bash
# Для ROS2 Humble
sudo apt install ros-humble-slam-toolbox

# Или из исходников (последняя версия)
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/SteveMacenski/slam_toolbox.git
cd ~/ros2_ws
colcon build --packages-select slam_toolbox
```

### Зависимости Python

```bash
pip install numpy
```

## Быстрый старт

### 1. Запуск всех компонентов

**Терминал 1: Лидар**
```bash
ros2 run watchdog_lidar lidar_node
```

**Терминал 2: SLAM**
```bash
ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  -p slam_toolbox.odom_frame:=odom \
  -p slam_toolbox.map_frame:=map \
  -p slam_toolbox.base_frame:=base_link \
  -p slam_toolbox.scan_topic:=/sensor/lidar/scan
```

**Терминал 3: Одометрия (STM32)**
```bash
ros2 run watchdog_stm32_interface stm32_interface_node
```

**Терминал 4: Навигация**
```bash
ros2 run watchdog_navigation navigation_node \
  --ros-args \
  -p use_slam:=true
```

### 2. Построение карты

1. **Двигайте робота** по пространству (вручную или командами)
2. **Карта строится автоматически** на основе данных лидара
3. **Просмотр карты** в RViz2:
   ```bash
   rviz2
   # Добавьте: Map → /map
   # Добавьте: LaserScan → /sensor/lidar/scan
   ```

### 3. Отправка цели

```bash
ros2 topic pub /navigation/goal geometry_msgs/msg/PoseStamped \
  "{header: {frame_id: 'map', stamp: {sec: 0}}, pose: {position: {x: 2.0, y: 1.0, z: 0.0}, orientation: {w: 1.0}}}"
```

## Детальная настройка

### Конфигурация SLAM

Создайте файл конфигурации для slam_toolbox:

```yaml
# ~/slam_config.yaml
slam_toolbox:
  ros__parameters:
    odom_frame: odom
    map_frame: map
    base_frame: base_link
    scan_topic: /sensor/lidar/scan
    mode: mapping  # или localization для локализации на известной карте
    
    # Параметры карты
    map_file_name: ""  # Для сохранения/загрузки карты
    map_start_pose: [0.0, 0.0, 0.0]
    
    # Разрешение карты
    resolution: 0.05  # 5 см на пиксель
    
    # Параметры сканирования
    max_laser_range: 12.0
    minimum_travel_distance: 0.2
    minimum_travel_heading: 0.2
    
    # Loop closure
    loop_search_maximum_distance: 3.0
```

Запуск с конфигом:
```bash
ros2 run slam_toolbox async_slam_toolbox_node \
  --ros-args \
  --params-file ~/slam_config.yaml
```

### Конфигурация навигации

```yaml
navigation:
  safety_distance: 0.3  # Безопасное расстояние до препятствий
  max_linear_velocity: 0.5  # Максимальная скорость движения
  max_angular_velocity: 1.0  # Максимальная скорость поворота
  goal_tolerance: 0.1  # Точность достижения цели
  use_slam: true  # Использовать SLAM
  inflation_radius: 0.3  # Радиус раздувания препятствий
```

## Работа с картами

### Сохранение карты

После построения карты сохраните её:

```bash
# Через сервис
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap \
  "{name: {data: '/home/user/maps/my_map'}}"
```

Это создаст файлы:
- `my_map.pgm` - изображение карты
- `my_map.yaml` - метаданные карты

### Загрузка карты для локализации

Для навигации по уже построенной карте:

```bash
ros2 run slam_toolbox localization_slam_toolbox_node \
  --ros-args \
  -p slam_toolbox.mode:=localization \
  -p slam_toolbox.map_file_name:="/home/user/maps/my_map.pgm" \
  -p slam_toolbox.scan_topic:=/sensor/lidar/scan
```

**Важно:** После загрузки карты нужно установить начальную позицию робота:
```bash
# В RViz2 используйте "2D Pose Estimate" tool
# Или через топик:
ros2 topic pub /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0}}}}"
```

## Процесс построения карты

### Пошаговая инструкция

1. **Подготовка**
   - Убедитесь, что лидар подключен и работает
   - Проверьте odometry: `ros2 topic echo /odom`
   - Запустите все узлы (лидар, SLAM, odometry, навигация)

2. **Исследование пространства**
   - Двигайте робота по всему пространству
   - Робот должен пройти по всем комнатам/зонам
   - Поворачивайте робота для сканирования углов

3. **Мониторинг**
   - Следите за картой в RViz2
   - Проверяйте, что карта покрывает все пространство
   - Убедитесь, что loop closure работает (замкнутые петли)

4. **Сохранение**
   - Когда карта готова, сохраните её
   - Проверьте качество карты в RViz2

### Советы для лучшей карты

1. **Медленное движение** - робот должен двигаться плавно
2. **Полное покрытие** - пройдите по всем зонам
3. **Повороты** - сканируйте углы и узкие места
4. **Loop closure** - вернитесь к начальной точке для замыкания петель
5. **Стабильность** - избегайте резких движений

## Решение проблем

### Проблема: "Карта не строится"

**Проверьте:**
1. Данные лидара: `ros2 topic echo /sensor/lidar/scan`
2. Odometry работает: `ros2 topic echo /odom`
3. SLAM узел запущен: `ros2 node list`
4. TF дерево: `ros2 run tf2_tools view_frames`

**Решение:**
- Убедитесь, что все топики публикуются
- Проверьте frame_id в сообщениях
- Двигайте робота - карта строится при движении

### Проблема: "Карта некачественная"

**Причины:**
- Недостаточно данных (робот мало двигался)
- Плохое качество лидара
- Проблемы с odometry

**Решение:**
- Увеличьте время исследования
- Проверьте калибровку лидара
- Улучшите odometry (энкодеры, IMU)

### Проблема: "Путь не найден"

**Проверьте:**
1. Карта загружена и актуальна
2. Цель в свободном пространстве
3. Стартовая позиция валидна

**Решение:**
- Проверьте карту в RViz2
- Попробуйте другую цель
- Уменьшите `inflation_radius`

### Проблема: "Неправильная локализация"

**Решение:**
- Установите начальную позицию через RViz2
- Используйте "2D Pose Estimate" tool
- Убедитесь, что odometry работает корректно

## Оптимизация производительности

### Для Raspberry Pi

```yaml
# Упрощенная конфигурация SLAM
resolution: 0.1  # Увеличить разрешение (меньше точность, больше скорость)
minimum_travel_distance: 0.3  # Реже обновления
minimum_travel_heading: 0.3
```

### Для мощных систем

```yaml
# Полная конфигурация
resolution: 0.05  # Высокое разрешение
minimum_travel_distance: 0.1  # Частые обновления
minimum_travel_heading: 0.1
```

## Интеграция с другими модулями

### Голосовые команды навигации

Можно добавить в `command_processor.py`:
```python
'go_to_room': {
    'patterns': ['иди в комнату', 'найди комнату'],
    'action': 'navigate_to_room',
    'params': {'room': 'living_room'},
}
```

### Интеграция с распознаванием лиц

Робот может запоминать места где видел лица:
```python
# При обнаружении лица, сохраняем позицию
if face_detected and person_id == 'owner':
    current_pose = slam_mapper.get_robot_position()
    save_landmark('owner_location', current_pose)
```

## Дополнительные ресурсы

- [SLAM Toolbox документация](https://github.com/SteveMacenski/slam_toolbox)
- [ROS2 Navigation Stack](https://navigation.ros.org/)
- [Cartographer (альтернатива)](https://google-cartographer-ros.readthedocs.io/)

