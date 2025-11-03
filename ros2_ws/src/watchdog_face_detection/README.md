# watchdog_face_detection

ROS2 пакет для детекции и распознавания лиц с базой данных.

## Функции

- **Детекция лиц** - обнаружение лиц на изображениях (OpenCV Haar, dlib, face_recognition)
- **Распознавание лиц** - создание эмбеддингов и сравнение лиц
- **База данных лиц** - хранение и управление базой данных известных лиц
- **Авторизация** - различение авторизованных и неавторизованных пользователей

## Установка зависимостей

```bash
pip install opencv-python face-recognition dlib
```

**Важно:** Для `face-recognition` требуется `dlib`, который может потребовать компиляции. На Ubuntu:

```bash
# Установка зависимостей для dlib
sudo apt-get update
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev libjpeg-dev

# Установка dlib и face-recognition
pip install dlib
pip install face-recognition
```

## Использование

### 1. Добавление лиц в базу данных

#### Из изображения

```bash
ros2 run watchdog_face_detection add_face_to_db \
  --image ~/my_photo.jpg \
  --id owner \
  --name "Мое Имя"
```

#### Из камеры (интерактивно)

```bash
ros2 run watchdog_face_detection add_face_to_db \
  --camera \
  --id owner \
  --name "Мое Имя" \
  --count 5
```

Утилита сделает несколько снимков (по умолчанию 5) для лучшей точности распознавания.

### 2. Запуск узла детекции

```bash
ros2 run watchdog_face_detection face_detection_node
```

С параметрами:
```bash
ros2 run watchdog_face_detection face_detection_node --ros-args \
  -p detection.method:=face_recognition \
  -p recognition.method:=face_recognition \
  -p recognition.threshold:=0.6 \
  -p database.path:=~/.watchdog_faces \
  -p camera.topic:=/camera/image_raw
```

### 3. Просмотр результатов

**Распознанные лица:**
```bash
ros2 topic echo /face_detection/detections
```

**Авторизованные лица:**
```bash
ros2 topic echo /face_detection/authorized
```

**Неизвестные лица:**
```bash
ros2 topic echo /face_detection/unknown
```

## Формат сообщений

### /face_detection/detections

```
person_id:name:confidence:x:y:width:height,person_id:name:...
```

Пример:
```
owner:Мое Имя:0.85:100:200:150:180,unknown:Unknown:0.0:400:300:120:140
```

### /face_detection/authorized

```
person_id:name:confidence
```

Пример:
```
owner:Мое Имя:0.85
```

### /face_detection/unknown

```
unknown
```

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `detection.method` | string | `face_recognition` | Метод детекции (haar, dlib, face_recognition) |
| `detection.model_path` | string | `""` | Путь к модели (для некоторых методов) |
| `recognition.method` | string | `face_recognition` | Метод распознавания |
| `recognition.threshold` | double | `0.6` | Порог схожести (ниже = строже) |
| `database.path` | string | `~/.watchdog_faces` | Путь к базе данных |
| `camera.topic` | string | `/camera/image_raw` | Топик изображений камеры |
| `processing.frame_skip` | int | `5` | Обрабатывать каждый N-й кадр |

## База данных лиц

База данных хранится в директории `~/.watchdog_faces` (по умолчанию).

**Структура:**
```
~/.watchdog_faces/
├── metadata.json        # Метаданные о лицах
└── embeddings/
    ├── owner.pkl        # Эмбеддинги владельца
    ├── friend1.pkl      # Эмбеддинги друга 1
    └── ...
```

**Управление базой:**

Можно вручную редактировать или использовать Python API:
```python
from watchdog_face_detection.face_database import FaceDatabase

db = FaceDatabase()
faces = db.list_faces()  # Список всех лиц
db.remove_face('person_id')  # Удаление лица
```

## Методы детекции

### face_recognition (рекомендуется)

**Преимущества:**
- Высокая точность
- Хорошая производительность
- Легко использовать

**Недостатки:**
- Требует компиляции dlib

### haar (OpenCV)

**Преимущества:**
- Быстрая работа
- Не требует дополнительных библиотек

**Недостатки:**
- Ниже точность
- Может пропускать лица под углом

### dlib HOG

**Преимущества:**
- Хорошая точность
- Средняя производительность

**Недостатки:**
- Требует dlib

## Настройка порога распознавания

**Для face_recognition:**
- `0.5` - Низкий (может путать похожих людей)
- `0.6` - Средний (рекомендуется)
- `0.7+` - Высокий (может не распознавать ваше лицо при плохом освещении)

## Советы для лучшей точности

1. **Добавляйте несколько снимков** - используйте опцию `--count 5-10` при добавлении лица
2. **Хорошее освещение** - убедитесь в равномерном освещении лица
3. **Разные углы** - добавьте снимки с разных ракурсов
4. **Разное освещение** - добавьте снимки при разном освещении
5. **Качество камеры** - используйте камеру хорошего качества

## Интеграция с другими модулями

### Использование распознанных лиц в контроллере

```python
# В watchdog_controller
from std_msgs.msg import String

def authorized_face_callback(self, msg: String):
    parts = msg.data.split(':')
    if len(parts) >= 2:
        person_id, name = parts[0], parts[1]
        if person_id == 'owner':
            # Выполняем действия для владельца
            pass
```

### Отслеживание лиц

Подпишитесь на `/face_detection/detections` и используйте координаты bbox для отслеживания.

## Отладка

### Проблема: "dlib не компилируется"

```bash
# Установите зависимости
sudo apt-get install build-essential cmake libopenblas-dev liblapack-dev

# Установите dlib
pip install dlib
```

### Проблема: "Лица не распознаются"

1. Проверьте, что лицо добавлено в базу
2. Снизьте порог распознавания
3. Добавьте больше снимков лица
4. Проверьте качество изображения с камеры

### Проблема: "Низкая производительность"

1. Увеличьте `frame_skip` (обрабатывать реже)
2. Используйте меньший размер изображения
3. Используйте метод `haar` вместо `face_recognition`

## Производительность

**Рекомендуемые конфигурации:**

**Raspberry Pi 4:**
```yaml
detection:
  method: "haar"  # Быстрее
processing:
  frame_skip: 10  # Реже обрабатывать
```

**Raspberry Pi 5 / NUC:**
```yaml
detection:
  method: "face_recognition"  # Точнее
processing:
  frame_skip: 5
```

**Мощная система (GPU):**
```yaml
detection:
  method: "face_recognition"
processing:
  frame_skip: 1  # Обрабатывать каждый кадр
```

## Расширение функционала

### Добавление поддержки InsightFace

InsightFace - более современный метод распознавания, требует дополнительной настройки:

```bash
pip install insightface onnxruntime
```

Затем используйте `recognition.method:=insightface` в параметрах.

### Интеграция с tracking

Можно добавить отслеживание лиц между кадрами для повышения производительности и точности.

