"""Модуль верификации голоса (Speaker Verification).

Проверяет, принадлежит ли голос авторизованному пользователю.
"""

import os
import pickle
import numpy as np
from typing import Optional, Tuple
from pathlib import Path
import rclpy
from rclpy.logging import get_logger


class VoiceVerifier:
    """Класс для верификации голоса."""

    def __init__(self, voice_sample_path: Optional[str] = None, threshold: float = 0.7):
        """Инициализирует верификатор голоса.

        Args:
            voice_sample_path: Путь к файлу с эталонным голосом
            threshold: Порог совпадения (0.0 - 1.0, выше = строже)
        """
        self.voice_sample_path = voice_sample_path
        self.threshold = threshold
        self.logger = get_logger('VoiceVerifier')
        self.reference_embedding = None
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Инициализирует модель распознавания голоса."""
        try:
            # Используем speechbrain для speaker verification
            from speechbrain.inference.speaker import SpeakerRecognition

            # Загружаем предобученную модель
            model_hub = 'speechbrain/spkrec-ecapa-voxceleb'
            self.model = SpeakerRecognition.from_hparams(
                source=model_hub,
                savedir=os.path.expanduser('~/models/speechbrain/spkrec-ecapa-voxceleb')
            )
            self.logger.info('Модель распознавания голоса загружена')

            # Загружаем эталонный голос, если указан
            if self.voice_sample_path and os.path.exists(self.voice_sample_path):
                self.load_reference_voice(self.voice_sample_path)

        except ImportError:
            self.logger.warn(
                'SpeechBrain не установлен. '
                'Для верификации голоса установите: pip install speechbrain'
            )
            self.model = None
        except Exception as e:
            self.logger.warn(f'Не удалось загрузить модель распознавания голоса: {e}')
            self.model = None

    def load_reference_voice(self, voice_sample_path: str) -> bool:
        """Загружает эталонный голос из файла.

        Args:
            voice_sample_path: Путь к аудио файлу с эталонным голосом

        Returns:
            True если успешно загружено
        """
        if not self.model:
            self.logger.warn('Модель не инициализирована')
            return False

        try:
            self.reference_embedding = self.model.encode_file(voice_sample_path)
            self.voice_sample_path = voice_sample_path
            self.logger.info(f'Эталонный голос загружен из {voice_sample_path}')
            return True
        except Exception as e:
            self.logger.error(f'Ошибка загрузки эталонного голоса: {e}')
            return False

    def verify(self, audio_data: bytes, sample_rate: int = 16000) -> Tuple[bool, float]:
        """Проверяет, принадлежит ли голос авторизованному пользователю.

        Args:
            audio_data: Байты аудио данных
            sample_rate: Частота дискретизации

        Returns:
            Кортеж (is_verified, confidence):
            - is_verified: True если голос совпадает
            - confidence: Уверенность (0.0 - 1.0)
        """
        if not self.model:
            self.logger.warn('Модель верификации не инициализирована')
            return True, 1.0  # Разрешаем, если модель не работает

        if self.reference_embedding is None:
            self.logger.warn('Эталонный голос не загружен')
            return True, 1.0  # Разрешаем, если эталон не задан

        try:
            # Создаем временный файл для аудио
            import tempfile
            import wave

            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            try:
                # Сохраняем аудио во временный файл
                with wave.open(tmp_path, 'wb') as wf:
                    wf.setnchannels(1)  # Mono
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(sample_rate)
                    wf.writeframes(audio_data)

                # Кодируем голос
                test_embedding = self.model.encode_file(tmp_path)

                # Вычисляем схожесть (cosine similarity)
                similarity = self._cosine_similarity(self.reference_embedding, test_embedding)
                is_verified = similarity >= self.threshold

                self.logger.debug(f'Верификация: similarity={similarity:.3f}, verified={is_verified}')

                return is_verified, float(similarity)

            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            self.logger.error(f'Ошибка верификации голоса: {e}')
            return False, 0.0

    def verify_from_file(self, audio_file: str) -> Tuple[bool, float]:
        """Проверяет голос из файла.

        Args:
            audio_file: Путь к аудио файлу

        Returns:
            Кортеж (is_verified, confidence)
        """
        try:
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            return self.verify(audio_data)
        except Exception as e:
            self.logger.error(f'Ошибка чтения файла {audio_file}: {e}')
            return False, 0.0

    @staticmethod
    def _cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Вычисляет косинусное расстояние между эмбеддингами.

        Args:
            emb1: Первый эмбеддинг
            emb2: Второй эмбеддинг

        Returns:
            Схожесть (0.0 - 1.0)
        """
        # Нормализуем векторы
        emb1_norm = emb1 / (np.linalg.norm(emb1) + 1e-8)
        emb2_norm = emb2 / (np.linalg.norm(emb2) + 1e-8)

        # Вычисляем косинусное расстояние
        similarity = np.dot(emb1_norm, emb2_norm.T)
        return float(np.clip(similarity, 0.0, 1.0))

    def save_reference_embedding(self, output_path: str) -> bool:
        """Сохраняет эталонный эмбеддинг в файл.

        Args:
            output_path: Путь для сохранения

        Returns:
            True если успешно
        """
        if self.reference_embedding is None:
            return False

        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                pickle.dump({
                    'embedding': self.reference_embedding,
                    'threshold': self.threshold,
                }, f)
            self.logger.info(f'Эталонный эмбеддинг сохранен в {output_path}')
            return True
        except Exception as e:
            self.logger.error(f'Ошибка сохранения эмбеддинга: {e}')
            return False

    def load_reference_embedding(self, input_path: str) -> bool:
        """Загружает эталонный эмбеддинг из файла.

        Args:
            input_path: Путь к файлу

        Returns:
            True если успешно
        """
        try:
            with open(input_path, 'rb') as f:
                data = pickle.load(f)
            self.reference_embedding = data['embedding']
            if 'threshold' in data:
                self.threshold = data['threshold']
            self.logger.info(f'Эталонный эмбеддинг загружен из {input_path}')
            return True
        except Exception as e:
            self.logger.error(f'Ошибка загрузки эмбеддинга: {e}')
            return False

