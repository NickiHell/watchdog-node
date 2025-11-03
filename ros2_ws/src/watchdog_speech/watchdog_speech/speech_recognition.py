"""Модуль распознавания речи (Speech-to-Text).

Поддерживает Vosk и Whisper для распознавания речи.
"""

import os
import json
import wave
import tempfile
from typing import Optional
from pathlib import Path
import rclpy
from rclpy.logging import get_logger


class SpeechRecognizer:
    """Класс для распознавания речи."""

    def __init__(self, model_type: str = 'vosk', model_path: Optional[str] = None, language: str = 'ru'):
        """Инициализирует распознаватель речи.

        Args:
            model_type: Тип модели ('vosk' или 'whisper')
            model_path: Путь к модели
            language: Язык распознавания ('ru', 'en')
        """
        self.model_type = model_type.lower()
        self.model_path = model_path
        self.language = language
        self.logger = get_logger('SpeechRecognizer')
        self.model = None
        self.recognizer = None
        self._initialize_model()

    def _initialize_model(self):
        """Инициализирует модель распознавания."""
        try:
            if self.model_type == 'vosk':
                self._init_vosk()
            elif self.model_type == 'whisper':
                self._init_whisper()
            else:
                raise ValueError(f'Неизвестный тип модели: {self.model_type}')
        except Exception as e:
            self.logger.error(f'Ошибка инициализации модели распознавания: {e}')
            self.model = None

    def _init_vosk(self):
        """Инициализирует модель Vosk."""
        try:
            import vosk
            from vosk import Model, SetLogLevel

            SetLogLevel(-1)  # Отключаем логи Vosk

            if self.model_path and os.path.exists(self.model_path):
                model_path = self.model_path
            else:
                # Пытаемся найти модель в стандартных местах
                default_paths = [
                    os.path.expanduser('~/models/vosk-model-small-ru-0.22'),
                    os.path.expanduser('~/models/vosk-model-ru-0.22'),
                    '/usr/share/vosk-models/vosk-model-small-ru-0.22',
                ]
                model_path = None
                for path in default_paths:
                    if os.path.exists(path):
                        model_path = path
                        break

            if not model_path:
                raise FileNotFoundError(
                    'Модель Vosk не найдена. '
                    'Скачайте с https://alphacephei.com/vosk/models и укажите путь в конфиге'
                )

            self.model = Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(self.model, 16000)
            self.recognizer.SetWords(True)
            self.logger.info(f'Модель Vosk загружена из {model_path}')

        except ImportError:
            self.logger.error('Библиотека vosk не установлена. Установите: pip install vosk')
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации Vosk: {e}')
            raise

    def _init_whisper(self):
        """Инициализирует модель Whisper."""
        try:
            import whisper

            if self.model_path and os.path.exists(self.model_path):
                model_name = self.model_path
            else:
                # Используем базовую модель
                model_name = 'base'  # tiny, base, small, medium, large

            self.model = whisper.load_model(model_name)
            self.logger.info(f'Модель Whisper загружена: {model_name}')

        except ImportError:
            self.logger.error('Библиотека openai-whisper не установлена. Установите: pip install openai-whisper')
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации Whisper: {e}')
            raise

    def recognize(self, audio_data: bytes, sample_rate: int = 16000) -> Optional[str]:
        """Распознает речь из аудио данных.

        Args:
            audio_data: Байты аудио данных (WAV формат, 16kHz, mono, 16-bit)
            sample_rate: Частота дискретизации

        Returns:
            Распознанный текст или None в случае ошибки
        """
        if not self.model:
            self.logger.warn('Модель не инициализирована')
            return None

        try:
            if self.model_type == 'vosk':
                return self._recognize_vosk(audio_data, sample_rate)
            elif self.model_type == 'whisper':
                return self._recognize_whisper(audio_data, sample_rate)
        except Exception as e:
            self.logger.error(f'Ошибка распознавания: {e}')
            return None

    def _recognize_vosk(self, audio_data: bytes, sample_rate: int) -> Optional[str]:
        """Распознает речь используя Vosk."""
        try:
            # Vosk требует определенный формат, создаем временный WAV файл
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                # Записываем аудио во временный файл
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)

                # Читаем и распознаем
                with open(tmp_path, 'rb') as f:
                    wf = wave.open(f, 'rb')
                    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != 'NONE':
                        raise ValueError('Входной файл должен быть WAV формат mono PCM')

                    data = wf.readframes(4000)
                    full_text = ''

                    while len(data) > 0:
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            if 'text' in result and result['text']:
                                full_text += result['text'] + ' '
                        data = wf.readframes(4000)

                    # Получаем финальный результат
                    result = json.loads(self.recognizer.FinalResult())
                    if 'text' in result and result['text']:
                        full_text += result['text']

                    return full_text.strip() if full_text.strip() else None

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            self.logger.error(f'Ошибка распознавания Vosk: {e}')
            return None

    def _recognize_whisper(self, audio_data: bytes, sample_rate: int) -> Optional[str]:
        """Распознает речь используя Whisper."""
        try:
            import numpy as np
            import io
            import soundfile as sf

            # Конвертируем байты в numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0

            # Whisper ожидает float32 массив
            result = self.model.transcribe(
                audio_array,
                language=self.language if self.language != 'ru' else None,
                task='transcribe'
            )

            text = result.get('text', '').strip()
            return text if text else None

        except ImportError:
            self.logger.error('Требуется soundfile для Whisper. Установите: pip install soundfile')
            return None
        except Exception as e:
            self.logger.error(f'Ошибка распознавания Whisper: {e}')
            return None

    def recognize_from_file(self, audio_file: str) -> Optional[str]:
        """Распознает речь из файла.

        Args:
            audio_file: Путь к аудио файлу

        Returns:
            Распознанный текст или None
        """
        try:
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            return self.recognize(audio_data)
        except Exception as e:
            self.logger.error(f'Ошибка чтения файла {audio_file}: {e}')
            return None

