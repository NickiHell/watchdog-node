# Настройка модуля детекции и распознавания лиц

Подробное руководство по настройке распознавания лиц с базой данных.

## Быстрый старт

### 1. Установка зависимостей

```bash
# Установка системных зависимостей для dlib
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libjpeg-dev

# Установка Python библиотек
pip install opencv-python face-recognition dlib

# Установка ROS2 cv_bridge
sudo apt install ros-humble-cv-bridge
```

### 2. Добавление вашего лица в базу

#### Из изображения

```bash
ros2 run watchdog_face_detection add_face_to_db \
  --image ~/my_photo.jpg \
  --id owner \
  --name "Ваше Имя"
```

#### Из камеры (рекомендуется)

```bash
ros2 run watchdog_face_detection add_face_to_db \
  --camera \
  --id owner \
  --name "Ваше Имя" \
  --count 10
```

Утилита сделает несколько снимков (рекомендуется 5-10) для лучшей точности.

### 3. Запуск узла

```bash
ros2 run watchdog_face_detection face_detection_node
```

### 4. Проверка работы

```bash
# Просмотр распознанных лиц
ros2 topic echo /face_detection/detections

# Просмотр авторизованных лиц
ros2 topic echo /face_detection/authorized

# Просмотр неизвестных лиц
ros2 topic echo /face_detection/unknown
```

## Структура базы данных

База данных хранится в `~/.watchdog_faces`:

```
~/.watchdog_faces/
├── metadata.json           # Метаданные о лицах
└── embeddings/
    ├── owner.pkl          # Эмбеддинги владельца
    ├── friend1.pkl        # Эмбеддинги друга
    └── ...
```

## Управление базой данных

### Просмотр списка лиц

```python
from watchdog_face_detection.face_database import FaceDatabase

db = FaceDatabase()
faces = db.list_faces()
for face in faces:
    print(f"{face['person_id']}: {face['name']} ({face['embedding_count']} эмбеддингов)")
```

### Удаление лица

```python
db = FaceDatabase()
db.remove_face('person_id')
```

### Программное добавление

```python
from watchdog_face_detection.face_detector import FaceDetector
from watchdog_face_detection.face_recognizer import FaceRecognizer
from watchdog_face_detection.face_database import FaceDatabase
import cv2

# Загружаем изображение
image = cv2.imread('photo.jpg')

# Детектируем лицо
detector = FaceDetector()
boxes = detector.detect_faces(image)

if boxes:
    face_region = detector.extract_face_region(image, boxes[0])
    
    # Создаем эмбеддинг
    recognizer = FaceRecognizer()
    embedding = recognizer.encode_face(face_region)
    
    # Добавляем в базу
    database = FaceDatabase()
    database.add_face('owner', 'Ваше Имя', embedding)
```

## Методы детекции

### face_recognition (рекомендуется)

**Преимущества:**
- Высокая точность
- Хорошая производительность
- Простота использования

**Использование:**
```yaml
detection:
  method: "face_recognition"
```

### Haar Cascade

**Преимущества:**
- Очень быстрая работа
- Не требует дополнительных библиотек
- Работает на слабых системах

**Недостатки:**
- Ниже точность
- Проблемы с лицами под углом

**Использование:**
```yaml
detection:
  method: "haar"
```

### dlib HOG

**Преимущества:**
- Хорошая точность
- Средняя производительность

**Использование:**
```yaml
detection:
  method: "dlib"
```

## Настройка порога распознавания

Порог определяет, насколько похожи должны быть лица для распознавания.

### Для face_recognition

- `0.4-0.5` - Низкий (может путать похожих людей)
- `0.6` - Средний (рекомендуется)
- `0.7-0.8` - Высокий (строгий, может не распознавать при плохом освещении)

### Изменение порога

```bash
ros2 run watchdog_face_detection face_detection_node --ros-args \
  -p recognition.threshold:=0.7
```

## Советы для лучшей точности

### 1. Добавление лиц

- **Множественные снимки**: Используйте `--count 10` для создания 10 эмбеддингов
- **Разные углы**: Поверните голову влево, вправо, вверх, вниз
- **Разное освещение**: Снимите при разном освещении (днем, вечером, при разных лампах)
- **Разные выражения**: Улыбка, серьезное лицо, нейтральное
- **Очки/без очков**: Если носите очки, добавьте оба варианта

### 2. Качество изображений

- **Разрешение**: Минимум 200x200 пикселей для лица
- **Освещение**: Равномерное, без теней
- **Фокус**: Четкое изображение
- **Фон**: Простой фон предпочтительнее

### 3. Условия распознавания

- **Освещение**: Хорошее освещение улучшает точность
- **Расстояние**: Оптимальное расстояние 1-3 метра
- **Угол**: Лицо должно быть фронтально к камере
- **Размер лица**: Лицо должно занимать достаточную часть кадра

## Производительность

### Оптимизация для слабых систем

**Raspberry Pi 4:**
```yaml
detection:
  method: "haar"  # Быстрее face_recognition
recognition:
  method: "face_recognition"
processing:
  frame_skip: 10  # Обрабатывать реже
```

**Raspberry Pi 5:**
```yaml
detection:
  method: "face_recognition"
processing:
  frame_skip: 5
```

### Оптимизация для мощных систем

```yaml
detection:
  method: "face_recognition"
processing:
  frame_skip: 1  # Обрабатывать каждый кадр
```

## Интеграция с другими модулями

### Использование в контроллере

```python
# В watchdog_controller
from std_msgs.msg import String

class ControllerNode(Node):
    def __init__(self):
        # ...
        self.authorized_sub = self.create_subscription(
            String,
            '/face_detection/authorized',
            self.authorized_face_callback,
            10
        )
    
    def authorized_face_callback(self, msg: String):
        parts = msg.data.split(':')
        if len(parts) >= 2:
            person_id, name = parts[0], parts[1]
            if person_id == 'owner':
                # Владелец обнаружен - разрешаем команды
                self.owner_present = True
            else:
                # Другой авторизованный пользователь
                self.known_user_present = True
```

### Комбинация с голосовой верификацией

Используйте вместе с верификацией голоса для двойной проверки:

```python
# Проверяем и лицо, и голос
if face_authorized and voice_verified:
    # Выполняем команду
    pass
```

## Отладка

### Проблема: "dlib не компилируется"

```bash
# Установите все зависимости
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev libjpeg-dev

# Компилируйте dlib
pip install dlib --verbose
```

### Проблема: "Лица не распознаются"

1. **Проверьте базу данных:**
   ```bash
   ls -la ~/.watchdog_faces/embeddings/
   ```

2. **Проверьте качество снимков:**
   - Достаточное разрешение?
   - Хорошее освещение?
   - Лицо четкое?

3. **Снизьте порог:**
   ```bash
   -p recognition.threshold:=0.5
   ```

4. **Добавьте больше снимков:**
   ```bash
   --count 15
   ```

### Проблема: "Ошибочные распознавания"

1. **Повысьте порог:**
   ```bash
   -p recognition.threshold:=0.7
   ```

2. **Улучшите качество эмбеддингов:**
   - Добавьте больше разнообразных снимков
   - Используйте более качественные изображения

### Проблема: "Низкая производительность"

1. **Увеличьте frame_skip:**
   ```yaml
   processing:
     frame_skip: 10
   ```

2. **Используйте Haar вместо face_recognition:**
   ```yaml
   detection:
     method: "haar"
   ```

3. **Уменьшите разрешение камеры:**
   - Настройте камеру на меньшее разрешение

## Расширение функционала

### InsightFace (более современный метод)

```bash
pip install insightface onnxruntime
```

Затем:
```yaml
recognition:
  method: "insightface"
```

### Отслеживание лиц (tracking)

Можно добавить отслеживание лиц между кадрами для:
- Повышения производительности (не распознавать каждый кадр)
- Улучшения стабильности
- Отслеживания нескольких людей одновременно

### Сохранение изображений неизвестных лиц

Добавьте сохранение изображений неизвестных лиц для последующего анализа и добавления в базу.

