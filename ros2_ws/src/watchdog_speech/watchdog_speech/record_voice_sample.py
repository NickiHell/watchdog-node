"""Утилита для записи эталонного голоса пользователя."""

import argparse
import sys
import os
from pathlib import Path

from watchdog_speech.audio_capture import AudioCapture
from watchdog_speech.voice_verification import VoiceVerifier


def record_voice_sample(output_path: str, duration: float = 5.0, sample_rate: int = 16000):
    """Записывает образец голоса пользователя.

    Args:
        output_path: Путь для сохранения записи
        duration: Длительность записи в секундах
        sample_rate: Частота дискретизации
    """
    print(f'\n{"="*60}')
    print('Запись эталонного голоса для верификации')
    print(f'{"="*60}')
    print(f'Длительность: {duration} секунд')
    print(f'Частота дискретизации: {sample_rate} Hz')
    print(f'Выходной файл: {output_path}')
    print(f'\nГоворите после звукового сигнала...')
    print('(Нажмите Enter для начала записи)')
    input()

    try:
        # Инициализируем захват аудио
        audio_capture = AudioCapture(sample_rate=sample_rate)
        audio_capture.start_recording()

        # Звуковой сигнал
        print('\nЗАПИСЬ НАЧАЛАСЬ (говорите)...')
        print('', end='', flush=True)

        # Записываем заданное время
        import time
        import numpy as np

        frames = []
        start_time = time.time()

        while time.time() - start_time < duration:
            chunk = audio_capture.read_chunk(timeout=0.1)
            if chunk:
                frames.append(chunk)
                elapsed = time.time() - start_time
                print(f'\rЗаписано: {elapsed:.1f}с / {duration:.1f}с', end='', flush=True)

        audio_capture.stop_recording()

        # Объединяем фреймы
        audio_data = b''.join(frames)
        total_time = time.time() - start_time

        print(f'\rЗапись завершена ({total_time:.1f} секунд)')

        # Сохраняем файл
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if audio_capture.save_to_file(audio_data, str(output_file)):
            print(f'Файл сохранен: {output_file}')
            file_size = os.path.getsize(output_file)
            print(f'Размер файла: {file_size / 1024:.1f} KB')
        else:
            print('ОШИБКА: Ошибка сохранения файла')
            return False

        # Создаем эмбеддинг для проверки
        print('\nПроверка качества записи...')
        verifier = VoiceVerifier()
        if verifier.load_reference_voice(str(output_file)):
            print('Эмбеддинг голоса создан успешно')
            
            # Сохраняем эмбеддинг
            embedding_path = output_file.with_suffix('.pkl')
            if verifier.save_reference_embedding(str(embedding_path)):
                print(f'Эмбеддинг сохранен: {embedding_path}')
            
            print(f'\n{"="*60}')
            print('Эталонный голос записан и готов к использованию!')
            print(f'Аудио файл: {output_file}')
            print(f'Эмбеддинг: {embedding_path}')
            print(f'\nУкажите путь к файлу в конфиге:')
            print(f'  voice_sample_path: "{output_file}"')
            print(f'{"="*60}\n')
            return True
        else:
            print('ВНИМАНИЕ: Не удалось создать эмбеддинг (SpeechBrain может быть не установлен)')
            print('Вы все равно можете использовать аудио файл напрямую.')
            return True

    except KeyboardInterrupt:
        print('\n\nЗапись прервана пользователем')
        return False
    except Exception as e:
        print(f'\nОШИБКА: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(
        description='Запись эталонного голоса для верификации',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Записать 5 секунд голоса
  ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav

  # Записать 10 секунд
  ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav --duration 10

  # Использовать другую частоту дискретизации
  ros2 run watchdog_speech record_voice_sample ~/voice_sample.wav --sample-rate 48000
        """
    )

    parser.add_argument(
        'output_path',
        type=str,
        help='Путь для сохранения записи (WAV формат)'
    )

    parser.add_argument(
        '--duration',
        type=float,
        default=5.0,
        help='Длительность записи в секундах (по умолчанию: 5.0)'
    )

    parser.add_argument(
        '--sample-rate',
        type=int,
        default=16000,
        help='Частота дискретизации в Hz (по умолчанию: 16000)'
    )

    args = parser.parse_args()

    success = record_voice_sample(
        output_path=args.output_path,
        duration=args.duration,
        sample_rate=args.sample_rate
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

