# Настройка камеры для WatchDog Robot

Подробное руководство по выбору, подключению и настройке камеры.

## Выбор камеры

### Варианты для 360° обзора

**Вариант 1: Несколько USB камер (рекомендуется для начала)**
- 2-4 USB веб-камеры с широким углом обзора
- Простое подключение
- Низкая цена (~$20-50 каждая)
- Можно склеить изображения в панораму

**Вариант 2: Специализированная 360° камера**
- Insta360 ONE X2 (~$300)
- Качественное изображение
- Готовая панорама
- Требует специальные драйверы

**Вариант 3: Raspberry Pi Camera Module v3**
- Низкая цена (~$25)
- Хорошая интеграция с Raspberry Pi
- Широкоугольный объектив
- НЕ настоящий 360°, но хороший угол обзора

### Рекомендации

**Для начала:** Raspberry Pi Camera Module v3
- Дешево
- Хорошо работает с Raspberry Pi
- Достаточно для распознавания лиц

**Для 360°:** 2-3 USB камеры с широким углом
- Расположить по кругу на роботе
- Использовать склейку панорамы

## Подключение

### USB камера

1. Подключите камеру через USB
2. Проверьте: `ls -l /dev/video*`
3. Проверьте права: `sudo usermod -a -G video $USER`

### Raspberry Pi Camera

1. Подключите шлейф камеры к CSI порту
2. Включите камеру: `sudo raspi-config` → Interface Options → Camera → Enable
3. Перезагрузите: `sudo reboot`
4. Проверьте: `vcgencmd get_camera`

## Использование

### Базовая настройка

**USB камера:**
```bash
ros2 run watchdog_camera camera_node --ros-args \
  -p camera.type:=usb \
  -p camera.device_id:=0
```

**Raspberry Pi Camera:**
```bash
ros2 run watchdog_camera camera_node --ros-args \
  -p camera.type:=picamera
```

**Несколько камер:**
```bash
ros2 run watchdog_camera camera_node --ros-args \
  -p camera.type:=multi \
  -p camera.device_ids:="[0, 1]" \
  -p camera.stitch_panorama:=true
```

### Проверка работы

```bash
# Просмотр изображений
ros2 topic echo /camera/image_raw

# Визуализация
ros2 run image_view image_view image:=/camera/image_raw

# Или в RViz2
rviz2
# Add → Image → /camera/image_raw
```

## Оптимизация для распознавания лиц

### Рекомендуемые настройки

```yaml
camera:
  width: 1280  # Достаточно для распознавания лиц
  height: 720
  fps: 15  # 15 FPS достаточно для face detection
```

### Для лучшего качества

```yaml
camera:
  width: 1920
  height: 1080
  fps: 30  # Полный FPS
```

## Интеграция с распознаванием лиц

Камера автоматически работает с модулем распознавания лиц:

```bash
# Терминал 1: Камера
ros2 run watchdog_camera camera_node

# Терминал 2: Распознавание лиц
ros2 run watchdog_face_detection face_detection_node \
  --ros-args \
  -p camera.topic:=/camera/image_raw
```

## Решение проблем

### Камера не найдена

```bash
# Проверьте подключение
ls -l /dev/video*

# Проверьте права
groups  # Должна быть группа video

# Временное решение
sudo chmod 666 /dev/video0
```

### Низкое качество

1. Проверьте USB порт (USB 3.0 лучше)
2. Улучшите освещение
3. Используйте качественный кабель
4. Проверьте настройки камеры (автофокус)

### Задержка изображения

1. Уменьшите разрешение
2. Снизьте FPS
3. Используйте более мощный компьютер

## Калибровка камеры

Для точной работы с распознаванием и навигацией:

```bash
# Печать калибровочной шахматной доски
# Скачайте: https://github.com/opencv/opencv/blob/master/doc/pattern.png

ros2 run camera_calibration cameracalibrator \
  --size 8x6 \
  --square 0.025 \
  image:=/camera/image_raw \
  camera:=/camera

# После калибровки сохраните параметры
# Они используются для корректной работы распознавания
```

## Производительность

### Raspberry Pi 4

```yaml
camera:
  width: 1280
  height: 720
  fps: 15  # Снизить для экономии ресурсов
```

### Raspberry Pi 5

```yaml
camera:
  width: 1920
  height: 1080
  fps: 30  # Полный FPS
```

## Дополнительные возможности

### Сохранение изображений

```python
# В контроллере или отдельном узле
from sensor_msgs.msg import Image
from cv_bridge import CvBridge

def image_callback(self, msg: Image):
    cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
    timestamp = time.time()
    cv2.imwrite(f'/path/to/images/image_{timestamp}.jpg', cv_image)
```

### Обработка в реальном времени

Используйте модуль `ImageProcessor` для:
- Изменения яркости/контраста
- Обрезки изображения
- Поворота
- Других эффектов

