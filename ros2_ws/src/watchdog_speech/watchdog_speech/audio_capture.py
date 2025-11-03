"""Модуль захвата аудио с микрофона."""

import pyaudio
import wave
import threading
import queue
from typing import Optional, Callable
import rclpy
from rclpy.logging import get_logger


class AudioCapture:
    """Класс для захвата аудио с микрофона."""

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        chunk_size: int = 1024,
        format: int = pyaudio.paInt16
    ):
        """Инициализирует захват аудио.

        Args:
            sample_rate: Частота дискретизации
            channels: Количество каналов (1 = mono)
            chunk_size: Размер чанка для чтения
            format: Формат аудио (pyaudio.paInt16)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = format
        self.logger = get_logger('AudioCapture')

        self.audio = None
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None

    def start_recording(self, callback: Optional[Callable] = None):
        """Начинает запись с микрофона.

        Args:
            callback: Функция обратного вызова для обработки аудио чанков
        """
        if self.is_recording:
            self.logger.warn('Запись уже идет')
            return

        try:
            self.audio = pyaudio.PyAudio()

            # Находим индекс микрофона по умолчанию
            device_index = None
            try:
                device_info = self.audio.get_default_input_device_info()
                device_index = device_info['index']
                self.logger.info(f'Используется микрофон: {device_info["name"]}')
            except Exception as e:
                self.logger.warn(f'Не удалось определить микрофон по умолчанию: {e}')

            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=callback if callback else self._audio_callback
            )

            self.is_recording = True
            self.stream.start_stream()
            self.logger.info(f'Запись начата: {self.sample_rate}Hz, {self.channels}ch')

        except Exception as e:
            self.logger.error(f'Ошибка запуска записи: {e}')
            self.stop_recording()

    def stop_recording(self):
        """Останавливает запись."""
        self.is_recording = False

        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass
            self.audio = None

        self.logger.info('Запись остановлена')

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для обработки аудио чанков."""
        if self.is_recording:
            self.audio_queue.put(in_data)
        return (None, pyaudio.paContinue)

    def read_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """Читает один чанк аудио.

        Args:
            timeout: Таймаут ожидания (секунды)

        Returns:
            Байты аудио или None
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def record_until_silence(
        self,
        silence_threshold: float = 0.01,
        min_duration: float = 0.5,
        max_duration: float = 5.0,
        silence_duration: float = 1.0
    ) -> bytes:
        """Записывает аудио до наступления тишины.

        Args:
            silence_threshold: Порог тишины (0.0 - 1.0)
            min_duration: Минимальная длительность записи (секунды)
            max_duration: Максимальная длительность записи (секунды)
            silence_duration: Длительность тишины для остановки (секунды)

        Returns:
            Байты записанного аудио
        """
        import time
        import numpy as np

        frames = []
        silence_frames = 0
        silence_frame_threshold = int(self.sample_rate / self.chunk_size * silence_duration)
        min_frames = int(self.sample_rate / self.chunk_size * min_duration)
        max_frames = int(self.sample_rate / self.chunk_size * max_duration)

        start_time = time.time()

        while len(frames) < max_frames:
            chunk = self.read_chunk(timeout=0.1)
            if chunk:
                # Проверяем уровень громкости
                audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
                volume = np.abs(audio_data).mean() / 32768.0

                if volume > silence_threshold:
                    silence_frames = 0
                    frames.append(chunk)
                else:
                    silence_frames += 1
                    if len(frames) >= min_frames and silence_frames >= silence_frame_threshold:
                        break
                    frames.append(chunk)  # Сохраняем тишину тоже
            else:
                break

        # Объединяем все фреймы
        audio_bytes = b''.join(frames)
        duration = time.time() - start_time
        self.logger.debug(f'Записано {duration:.2f} секунд аудио')

        return audio_bytes

    def save_to_file(self, audio_data: bytes, filename: str) -> bool:
        """Сохраняет аудио данные в WAV файл.

        Args:
            audio_data: Байты аудио данных
            filename: Имя файла

        Returns:
            True если успешно
        """
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(self.audio.get_sample_size(self.format))
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data)
            self.logger.debug(f'Аудио сохранено в {filename}')
            return True
        except Exception as e:
            self.logger.error(f'Ошибка сохранения аудио: {e}')
            return False

