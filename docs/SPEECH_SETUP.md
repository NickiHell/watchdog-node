# Настройка модуля обработки речи

Подробное руководство по настройке распознавания речи, верификации голоса и синтеза речи.

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install vosk speechbrain silero soundfile pyaudio numpy torch openai-whisper
```

### 2. Установка моделей Vosk

```bash
# Создаем директорию для моделей
mkdir -p ~/models

# Скачиваем маленькую русскую модель (~40MB)
cd ~/models
wget https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
unzip vosk-model-small-ru-0.22.zip

# Или полную модель (~1.5GB, более точная)
# wget https://alphacephei.com/vosk/models/vosk-model-ru-0.22.zip
```

### 3. Запись эталонного голоса

```bash
# Запускаем утилиту записи
ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav

# Говорите после нажатия Enter
# Запись будет длиться 5 секунд
```

### 4. Запуск узла

```bash
ros2 run watchdog_speech speech_node --ros-args \
  -p recognition.model_path:=~/models/vosk-model-small-ru-0.22 \
  -p voice_verification.voice_sample_path:=~/voice_sample.wav
```

## Детальная настройка

### Распознавание речи (STT)

#### Vosk (рекомендуется)

**Преимущества:**
- Быстро работает на CPU
- Небольшой размер модели
- Хорошее качество для русского языка
- Работает офлайн

**Установка:**
```bash
pip install vosk
```

**Модели:**
- Маленькая: `vosk-model-small-ru-0.22` (~40MB, быстрая)
- Полная: `vosk-model-ru-0.22` (~1.5GB, более точная)

**Конфигурация:**
```yaml
recognition:
  model: "vosk"
  model_path: "~/models/vosk-model-small-ru-0.22"
  language: "ru"
```

#### Whisper

**Преимущества:**
- Очень высокое качество
- Поддержка множества языков
- Работает офлайн

**Недостатки:**
- Медленнее Vosk
- Требует больше памяти

**Установка:**
```bash
pip install openai-whisper
```

**Конфигурация:**
```yaml
recognition:
  model: "whisper"
  model_path: ""  # Автозагрузка, можно указать tiny/base/small/medium/large
  language: "ru"
```

### Верификация голоса

**Требования:**
- SpeechBrain (автоматически скачает модели)
- Эталонный голос (записанный через `record_voice_sample`)

**Установка:**
```bash
pip install speechbrain
```

**Запись эталонного голоса:**
```bash
# Базовая запись (5 секунд)
ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav

# Длинная запись для лучшей точности
ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav --duration 10

# Высокое качество
ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav \
  --duration 10 \
  --sample-rate 48000
```

**Советы для лучшей точности:**
1. Записывайте в тихом месте
2. Используйте качественный микрофон
3. Говорите четко и естественно
4. Запишите 2-3 варианта в разных условиях
5. Используйте записи длиной 10+ секунд

**Настройка порога:**
```yaml
voice_verification:
  enabled: true
  voice_sample_path: "~/voice_sample.wav"
  threshold: 0.7  # 0.5-0.9, выше = строже
```

**Пороги:**
- `0.5-0.6` - Низкий (может принимать других)
- `0.7-0.8` - Средний (рекомендуется)
- `0.9+` - Высокий (может отклонять ваш голос)

### Синтез речи (TTS)

#### Silero (рекомендуется)

**Преимущества:**
- Отличное качество для русского
- Быстрая работа
- Несколько голосов на выбор

**Установка:**
```bash
pip install torch
# Модели загружаются автоматически при первом использовании
```

**Доступные голоса (русский):**
- `aidar` - мужской
- `baya` - женский
- `kseniya` - женский
- `xenia` - женский
- `eugene` - мужской

**Конфигурация:**
```yaml
synthesis:
  model: "silero"
  speaker: "aidar"
  device: "cpu"  # или "cuda" для GPU
```

#### speakerpy

**Преимущества:**
- Уже установлен в проекте
- Легковесный

**Конфигурация:**
```yaml
synthesis:
  model: "speakerpy"
  model_id: "ru_v3"
  speaker: "kelthuzad"
```

### Захват аудио

**Зависимости:**
```bash
pip install pyaudio
```

**Проверка микрофона:**
```bash
# Список устройств
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"
```

**Конфигурация:**
```yaml
audio:
  sample_rate: 16000  # 16000 для Vosk, 48000 для лучшего качества
  listen_mode: "continuous"  # continuous или push_to_talk
  silence_threshold: 0.01  # Порог для остановки записи
```

## Решение проблем

### Проблема: "Модель не найдена"

**Решение:**
```bash
# Проверьте путь к модели
ls ~/models/vosk-model-small-ru-0.22

# Укажите полный путь в конфиге
recognition.model_path: "/home/user/models/vosk-model-small-ru-0.22"
```

### Проблема: "Микрофон не найден"

**Решение:**
```bash
# Проверьте доступные устройства
python3 -c "import pyaudio; p = pyaudio.PyAudio(); [print(i, p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"

# Установите alsa-utils (для Linux)
sudo apt install alsa-utils portaudio19-dev python3-pyaudio
```

### Проблема: "SpeechBrain не работает"

**Решение:**
```bash
# Переустановите
pip uninstall speechbrain
pip install speechbrain

# Или отключите верификацию временно
voice_verification.enabled: false
```

### Проблема: "Низкая точность распознавания"

**Решения:**
1. Используйте модель большего размера (полная модель Vosk)
2. Улучшите качество микрофона
3. Снизьте фоновый шум
4. Говорите четче и медленнее
5. Используйте Whisper вместо Vosk

### Проблема: "Верификация не работает"

**Решения:**
1. Запишите новый эталонный голос
2. Снизьте порог верификации (threshold)
3. Используйте более длинную запись (10+ секунд)
4. Убедитесь, что говорите в тех же условиях, что и при записи

## Производительность

### Рекомендуемые конфигурации

**Бюджетная (Raspberry Pi 4):**
```yaml
recognition:
  model: "vosk"
  model_path: "~/models/vosk-model-small-ru-0.22"
synthesis:
  model: "silero"
  device: "cpu"
voice_verification:
  enabled: false  # Отключить для экономии ресурсов
```

**Оптимальная (Raspberry Pi 5 / NUC):**
```yaml
recognition:
  model: "vosk"
  model_path: "~/models/vosk-model-ru-0.22"
synthesis:
  model: "silero"
  device: "cpu"
voice_verification:
  enabled: true
  threshold: 0.7
```

**Мощная (Jetson Nano / Desktop с GPU):**
```yaml
recognition:
  model: "whisper"
  model_path: "base"
synthesis:
  model: "silero"
  device: "cuda"
voice_verification:
  enabled: true
  threshold: 0.8
```

## Тестирование

### Тест распознавания

```bash
# Запустите узел
ros2 run watchdog_speech speech_node

# В другом терминале просматривайте распознанный текст
ros2 topic echo /speech/recognized_text

# Говорите в микрофон и проверяйте результат
```

### Тест верификации

```bash
# Запишите эталон
ros2 run watchdog_speech record_voice_sample ~/test_voice.wav

# Запустите узел с верификацией
ros2 run watchdog_speech speech_node --ros-args \
  -p voice_verification.voice_sample_path:=~/test_voice.wav

# Просматривайте статус
ros2 topic echo /speech/verification_status

# Говорите - должны увидеть verified или rejected
```

### Тест синтеза

```bash
# Отправьте текст для синтеза
ros2 topic pub /speech/synthesis_request std_msgs/msg/String "data: 'Привет, это тест синтеза речи'"
```

