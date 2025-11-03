"""Модуль синтеза речи (Text-to-Speech).

Поддерживает speakerpy и Silero для синтеза речи.
"""

import os
import tempfile
from typing import Optional
import rclpy
from rclpy.logging import get_logger


class SpeechSynthesizer:
    """Класс для синтеза речи."""

    def __init__(
        self,
        model_type: str = 'silero',
        model_id: str = 'ru_v3',
        language: str = 'ru',
        speaker: str = 'aidar',
        device: str = 'cpu',
        sample_rate: int = 48000
    ):
        """Инициализирует синтезатор речи.

        Args:
            model_type: Тип модели ('silero' или 'speakerpy')
            model_id: ID модели (для Silero)
            language: Язык ('ru', 'en')
            speaker: Имя голоса
            device: Устройство ('cpu', 'cuda')
            sample_rate: Частота дискретизации
        """
        self.model_type = model_type.lower()
        self.model_id = model_id
        self.language = language
        self.speaker = speaker
        self.device = device
        self.sample_rate = sample_rate
        self.logger = get_logger('SpeechSynthesizer')
        self.model = None
        self.synthesizer = None
        self._initialize_model()

    def _initialize_model(self):
        """Инициализирует модель синтеза."""
        try:
            if self.model_type == 'silero':
                self._init_silero()
            elif self.model_type == 'speakerpy':
                self._init_speakerpy()
            else:
                raise ValueError(f'Неизвестный тип модели: {self.model_type}')
        except Exception as e:
            self.logger.error(f'Ошибка инициализации модели синтеза: {e}')
            self.model = None

    def _init_silero(self):
        """Инициализирует модель Silero."""
        try:
            import torch
            import os

            self.device = torch.device(self.device)
            
            # Silero загружается через torch.hub
            self.model, example_text = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language=self.language,
                speaker=self.speaker
            )
            self.model.to(self.device)
            self.sample_rate = 48000  # Silero использует 48kHz
            self.logger.info(f'Модель Silero загружена: speaker={self.speaker}, device={self.device}')

        except ImportError:
            self.logger.error(
                'Библиотека torch не установлена. '
                'Установите: pip install torch'
            )
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации Silero: {e}')
            raise

    def _init_speakerpy(self):
        """Инициализирует модель speakerpy."""
        try:
            from speakerpy.lib_speak import Speaker
            from speakerpy.lib_sl_text import SeleroText

            self.synthesizer = Speaker(
                model_id=self.model_id,
                language=self.language,
                speaker=self.speaker,
                device=self.device
            )
            self.logger.info(f'Модель speakerpy загружена: speaker={self.speaker}')

        except ImportError:
            self.logger.error(
                'Библиотека speakerpy не установлена. '
                'Установите: pip install speakerpy'
            )
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации speakerpy: {e}')
            raise

    def synthesize(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Синтезирует речь из текста.

        Args:
            text: Текст для синтеза
            output_file: Путь для сохранения аудио (опционально)

        Returns:
            Байты аудио данных (WAV формат) или None в случае ошибки
        """
        if not text or not text.strip():
            self.logger.warn('Пустой текст для синтеза')
            return None

        if self.model_type == 'silero':
            if self.model is None:
                return None
            return self._synthesize_silero(text, output_file)
        elif self.model_type == 'speakerpy':
            if self.synthesizer is None:
                return None
            return self._synthesize_speakerpy(text, output_file)

        return None

    def _synthesize_silero(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Синтезирует речь используя Silero."""
        try:
            import torch
            import soundfile as sf
            import io

            # Генерируем аудио
            audio_list = self.model.apply_tts(
                texts=[text],
                speaker=self.speaker,
                sample_rate=self.sample_rate
            )
            
            # Берем первый элемент (Silero возвращает список)
            audio = audio_list[0] if isinstance(audio_list, list) else audio_list

            # Конвертируем в numpy array и затем в байты
            if isinstance(audio, torch.Tensor):
                audio_np = audio.cpu().numpy()
            else:
                audio_np = audio

            # Сохраняем в буфер
            buffer = io.BytesIO()
            sf.write(buffer, audio_np, self.sample_rate, format='WAV')
            audio_bytes = buffer.getvalue()

            # Сохраняем в файл, если указан
            if output_file:
                os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
                with open(output_file, 'wb') as f:
                    f.write(audio_bytes)
                self.logger.debug(f'Аудио сохранено в {output_file}')

            return audio_bytes

        except ImportError:
            self.logger.error('Требуется soundfile для Silero. Установите: pip install soundfile')
            return None
        except Exception as e:
            self.logger.error(f'Ошибка синтеза Silero: {e}')
            return None

    def _synthesize_speakerpy(self, text: str, output_file: Optional[str] = None) -> Optional[bytes]:
        """Синтезирует речь используя speakerpy."""
        try:
            from speakerpy.lib_sl_text import SeleroText
            import wave
            import numpy as np
            import io

            # Подготавливаем текст
            selero_text = SeleroText(text)

            # Синтезируем речь
            audio_data = self.synthesizer.speak(
                text=selero_text,
                sample_rate=self.sample_rate,
                speed=1.0
            )

            # Конвертируем в байты WAV
            # speakerpy возвращает numpy array
            if hasattr(audio_data, 'numpy'):
                audio_np = audio_data.numpy()
            else:
                audio_np = np.array(audio_data)

            # Нормализуем до 16-bit PCM
            audio_np = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)

            # Создаем WAV в памяти
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_np.tobytes())

            audio_bytes = buffer.getvalue()

            # Сохраняем в файл, если указан
            if output_file:
                os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
                with open(output_file, 'wb') as f:
                    f.write(audio_bytes)
                self.logger.debug(f'Аудио сохранено в {output_file}')

            return audio_bytes

        except Exception as e:
            self.logger.error(f'Ошибка синтеза speakerpy: {e}')
            return None

    def speak(self, text: str) -> bool:
        """Воспроизводит речь через аудио систему.

        Args:
            text: Текст для воспроизведения

        Returns:
            True если успешно
        """
        try:
            import subprocess
            import tempfile

            # Синтезируем в временный файл
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                audio_bytes = self.synthesize(text, tmp_path)
                if not audio_bytes:
                    return False

                # Воспроизводим через системный плеер
                # Проверяем доступные плееры
                players = ['aplay', 'paplay', 'play', 'ffplay']
                player = None
                for p in players:
                    if subprocess.run(['which', p], capture_output=True).returncode == 0:
                        player = p
                        break

                if player:
                    subprocess.run([player, tmp_path], check=False)
                    return True
                else:
                    self.logger.warn('Не найден аудио плеер для воспроизведения')
                    return False

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            self.logger.error(f'Ошибка воспроизведения: {e}')
            return False

