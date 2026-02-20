# watchdog_camera

ROS2 пакет для захвата и публикации изображений с камеры.

## Функции

- **Захват изображений** - работа с USB камерами, Raspberry Pi Camera
- **Поддержка нескольких камер** - для создания 360° эффекта
- **Публикация в ROS2** - стандартные сообщения Image
- **Обработка изображений** - различные эффекты и коррекция

## Поддерживаемые камеры

### USB камеры

Любые USB веб-камеры, поддерживаемые OpenCV:
- Logitech C920/C930
- Веб-камеры USB 2.0/3.0
- IP камеры через USB адаптер

### Raspberry Pi Camera Module

- Raspberry Pi Camera Module v2
- Raspberry Pi Camera Module v3
- Любые совместимые камеры через CSI интерфейс

### Несколько камер (360°)

- Комбинация нескольких USB камер
- Возможность склейки в панораму

## Установка зависимостей

```bash
# OpenCV
pip install opencv-python

# cv_bridge для ROS2
sudo apt install ros-humble-cv-bridge
```

Для Raspberry Pi Camera может потребоваться:
```bash
sudo apt install python3-picamera2  # Для новых версий Pi
# Или настройка через raspi-config
sudo raspi-config
# Interface Options → Camera → Enable
```

## Использование

### USB камера

```bash
ros2 run watchdog_camera camera_node --ros-args \
  -p camera.type:=usb \
  -p camera.device_id:=0 \
  -p camera.width:=1920 \
  -p camera.height:=1080 \
  -p camera.fps:=30
```

### Raspberry Pi Camera

```bash
ros2 run watchdog_camera camera_node --ros-args \
  -p camera.type:=picamera \
  -p camera.width:=1920 \
  -p camera.height:=1080
```

### Несколько камер (360°)

```bash
ros2 run watchdog_camera camera_node --ros-args \
  -p camera.type:=multi \
  -p camera.device_ids:="[0, 1]" \
  -p camera.stitch_panorama:=true
```

## Проверка работы

```bash
# Просмотр изображений
ros2 topic echo /camera/image_raw

# Визуализация в RViz2
rviz2
# Add → By topic → /camera/image_raw → Image

# Или использование image_view
ros2 run image_view image_view image:=/camera/image_raw
```

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `camera.type` | string | `usb` | Тип камеры (usb, picamera, multi) |
| `camera.device_id` | int | `0` | ID USB камеры |
| `camera.device_ids` | int[] | `[0, 1]` | Список ID для multi режима |
| `camera.width` | int | `1920` | Ширина изображения |
| `camera.height` | int | `1080` | Высота изображения |
| `camera.fps` | int | `30` | Частота кадров |
| `camera.frame_id` | string | `camera_frame` | Имя фрейма |
| `camera.topic` | string | `/camera/image_raw` | Топик для публикации |
| `camera.stitch_panorama` | bool | `false` | Склеивать ли изображения |

## Топики

### Публикации

- `/camera/image_raw` (sensor_msgs/Image) - Изображения с камеры
- `/camera/camera_info` (sensor_msgs/CameraInfo) - Информация о камере

## Интеграция с другими модулями

### Распознавание лиц

Изображения автоматически используются узлом `face_detection_node`:
```bash
# Камера публикует в /camera/image_raw
# face_detection_node подписывается на этот топик
ros2 run watchdog_face_detection face_detection_node \
  --ros-args \
  -p camera.topic:=/camera/image_raw
```

### Обработка в контроллере

```python
# Подписка на изображения
self.image_sub = self.create_subscription(
    Image,
    '/camera/image_raw',
    self.image_callback,
    10
)
```

## Настройка Raspberry Pi Camera

### Включение камеры

```bash
sudo raspi-config
# Interface Options → Camera → Enable
# Перезагрузите Raspberry Pi
```

### Проверка работы

```bash
# Проверка через v4l2
v4l2-ctl --list-devices

# Или через Python
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera failed')"
```

## Решение проблем

### Проблема: "Камера не открывается"

**Проверьте:**
```bash
# Список доступных камер
ls -l /dev/video*

# Проверка прав доступа
ls -l /dev/video0
# Должно быть: crw-rw---- или crw-rw-rw-

# Добавьте в группу video
sudo usermod -a -G video $USER
# Перелогиньтесь
```

### Проблема: "Низкое качество изображения"

1. Увеличьте разрешение: `-p camera.width:=1920 -p camera.height:=1080`
2. Проверьте USB порт (USB 3.0 для высокого разрешения)
3. Убедитесь в достаточной освещенности

### Проблема: "Задержка в изображении"

1. Уменьшите разрешение
2. Уменьшите FPS: `-p camera.fps:=15`
3. Для Pi Camera: установите `buffersize=1`

### Проблема: "Pi Camera не работает"

1. Проверьте подключение шлейфа
2. Убедитесь, что камера включена в raspi-config
3. Попробуйте другой device_id (обычно 0)

## Оптимизация производительности

### Для Raspberry Pi

```yaml
camera:
  width: 1280
  height: 720
  fps: 15  # Снизить FPS
```

### Для мощных систем

```yaml
camera:
  width: 1920
  height: 1080
  fps: 30  # Полный FPS
```

## Расширение функционала

### Добавление обработки изображений

Используйте модуль `ImageProcessor`:
```python
from watchdog_camera.image_processor import ImageProcessor

processor = ImageProcessor()
processed = processor.adjust_brightness(frame, 0.1)
```

### Калибровка камеры

Для получения правильных параметров камеры используйте:
```bash
ros2 run camera_calibration cameracalibrator \
  --size 8x6 \
  --square 0.025 \
  image:=/camera/image_raw
```

### Сохранение изображений

Подпишитесь на топик и сохраняйте:
```python
def image_callback(self, msg: Image):
    cv_image = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
    cv2.imwrite(f'image_{time.time()}.jpg', cv_image)
```

## Советы

1. **Качество кабеля** - для USB камер используйте качественный USB кабель
2. **Освещение** - хорошее освещение улучшает качество
3. **Фокус** - для автофокуса используйте качественные камеры
4. **Стабильность** - закрепите камеру надежно на роботе
