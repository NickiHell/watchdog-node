# watchdog_speech

ROS2 пакет для распознавания речи, верификации голоса и синтеза речи.

## Функции

- **Распознавание речи (STT)** - преобразование речи в текст (Vosk, Whisper)
- **Верификация голоса** - проверка, что команды дает авторизованный пользователь
- **Синтез речи (TTS)** - преобразование текста в речь (Silero, speakerpy)
- **Обработка голосовых команд** - распознавание и выполнение команд

## Установка зависимостей

```bash
pip install vosk speechbrain silero soundfile pyaudio numpy torch openai-whisper
```

Или используйте `requirements.txt` из корня проекта.

### Установка моделей

**Vosk (рекомендуется для начала):**
```bash
# Скачайте модель с https://alphacephei.com/vosk/models
# Русская маленькая модель (~40MB)
wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
unzip vosk-model-small-ru-0.22.zip -d ~/models/

# Или полная модель (~1.5GB, более точная)
wget https://alphacephei.com/vosk/models/vosk-model-ru-0.22.zip
```

**Whisper:**
Модели загружаются автоматически при первом использовании.

**SpeechBrain (для верификации голоса):**
Модели загружаются автоматически при первом использовании.

## Использование

### 1. Запись эталонного голоса

Перед использованием нужно записать эталонный голос:

```bash
ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav
```

Утилита:
- Записывает ваш голос в течение 5 секунд (или указанного времени)
- Создает эмбеддинг для верификации
- Сохраняет файлы для использования

Параметры:
```bash
ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav \
  --duration 10 \
  --sample-rate 16000
```

### 2. Запуск узла

```bash
ros2 run watchdog_speech speech_node
```

С параметрами:
```bash
ros2 run watchdog_speech speech_node --ros-args \
  -p recognition.model:=vosk \
  -p recognition.model_path:=~/models/vosk-model-small-ru-0.22 \
  -p voice_verification.enabled:=true \
  -p voice_verification.voice_sample_path:=~/voice_sample.wav \
  -p voice_verification.threshold:=0.7 \
  -p synthesis.model:=silero \
  -p synthesis.speaker:=aidar
```

### 3. Проверка работы

**Просмотр распознанного текста:**
```bash
ros2 topic echo /speech/recognized_text
```

**Просмотр статуса верификации:**
```bash
ros2 topic echo /speech/verification_status
```

**Отправка текста для синтеза:**
```bash
ros2 topic pub /speech/synthesis_request std_msgs/msg/String "data: 'Привет, это тест'"
```

## Поддерживаемые команды

### Движение
- "вперед", "ехать вперед", "двигайся вперед" - движение вперед
- "назад", "ехать назад" - движение назад
- "влево", "налево", "поверни влево" - поворот влево
- "вправо", "направо", "поверни вправо" - поворот вправо
- "стоп", "остановись" - остановка

### Режимы
- "следуй за мной", "следуй" - режим следования
- "режим ожидания", "жду" - режим простоя

### Другое
- "привет", "здравствуй" - приветствие

## Добавление пользовательских команд

Используйте `command_processor.py` для добавления новых команд:

```python
command_processor.add_custom_command(
    name='custom_action',
    patterns=['паттерн1', 'паттерн2'],
    action='custom',
    params={'param1': value1}
)
```

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `recognition.model` | string | `vosk` | Модель распознавания (vosk, whisper) |
| `recognition.model_path` | string | `""` | Путь к модели |
| `recognition.language` | string | `ru` | Язык распознавания |
| `voice_verification.enabled` | bool | `true` | Включить верификацию |
| `voice_verification.voice_sample_path` | string | `""` | Путь к эталону |
| `voice_verification.threshold` | double | `0.7` | Порог совпадения |
| `synthesis.model` | string | `silero` | Модель синтеза |
| `synthesis.speaker` | string | `aidar` | Голос синтезатора |
| `audio.listen_mode` | string | `continuous` | Режим прослушивания |
| `audio.silence_threshold` | double | `0.01` | Порог тишины |

## Топики

### Публикации
- `/speech/recognized_text` (std_msgs/String) - Распознанный текст
- `/speech/verification_status` (std_msgs/String) - Статус верификации
- `/cmd_vel` (geometry_msgs/Twist) - Команды движения

### Подписки
- `/speech/synthesis_request` (std_msgs/String) - Запрос синтеза речи

## Настройка верификации голоса

### Порог верификации

- `0.5-0.6` - Низкий (может принимать других людей)
- `0.7-0.8` - Средний (рекомендуется)
- `0.9+` - Высокий (может отклонять ваш голос при шуме)

### Улучшение точности

1. Запишите несколько образцов в разных условиях (тихо, с шумом)
2. Используйте более длинные записи (10+ секунд)
3. Говорите четко и в одном темпе
4. Убедитесь в хорошем качестве микрофона

## Отладка

### Проблемы с микрофоном

```bash
# Проверить доступные устройства
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"
```

### Проблемы с распознаванием

- Убедитесь, что модель загружена правильно
- Проверьте частоту дискретизации (должна быть 16kHz для Vosk)
- Проверьте качество записи (микрофон, шум)

### Проблемы с верификацией

- Убедитесь, что SpeechBrain установлен
- Проверьте, что эталонный голос записан правильно
- Попробуйте снизить порог верификации

## Замечания

- Для верификации голоса требуется SpeechBrain (тяжелая библиотека)
- Vosk работает быстро и эффективно на CPU
- Whisper более точный, но медленнее
- Silero TTS работает только на CPU (или с CUDA)
- Для работы в реальном времени рекомендуется Vosk + Silero

