"""Утилита для добавления лиц в базу данных."""

import argparse
import sys
import os
import cv2
import numpy as np
from pathlib import Path

from watchdog_face_detection.face_detector import FaceDetector
from watchdog_face_detection.face_recognizer import FaceRecognizer
from watchdog_face_detection.face_database import FaceDatabase


def add_face_from_image(
    image_path: str,
    person_id: str,
    name: str,
    database_path: str = '~/.watchdog_faces',
    detection_method: str = 'face_recognition',
    recognition_method: str = 'face_recognition'
):
    """Добавляет лицо из изображения в базу данных.

    Args:
        image_path: Путь к изображению
        person_id: Уникальный ID человека
        name: Имя человека
        database_path: Путь к базе данных
        detection_method: Метод детекции
        recognition_method: Метод распознавания
    """
    print(f'\n{"="*60}')
    print('Добавление лица в базу данных')
    print(f'{"="*60}')
    print(f'Изображение: {image_path}')
    print(f'ID: {person_id}')
    print(f'Имя: {name}')
    print(f'База данных: {database_path}')

    # Проверяем существование файла
    if not os.path.exists(image_path):
        print(f'❌ Файл не найден: {image_path}')
        return False

    try:
        # Загружаем изображение
        image = cv2.imread(image_path)
        if image is None:
            print(f'❌ Не удалось загрузить изображение: {image_path}')
            return False

        print(f'✅ Изображение загружено: {image.shape[1]}x{image.shape[0]}')

        # Инициализируем детектор и распознаватель
        print('\n🔍 Инициализация детектора и распознавателя...')
        face_detector = FaceDetector(method=detection_method)
        face_recognizer = FaceRecognizer(method=recognition_method)

        # Обнаруживаем лица
        print('🔍 Поиск лиц на изображении...')
        face_boxes = face_detector.detect_faces(image)

        if not face_boxes:
            print('❌ Лица не найдены на изображении')
            print('💡 Попробуйте использовать более четкое изображение с хорошо видимым лицом')
            return False

        print(f'✅ Найдено лиц: {len(face_boxes)}')

        # Используем первое найденное лицо
        if len(face_boxes) > 1:
            print(f'⚠️  Найдено несколько лиц, используется первое')

        face_box = face_boxes[0]
        print(f'📐 Координаты: x={face_box[0]}, y={face_box[1]}, w={face_box[2]}, h={face_box[3]}')

        # Извлекаем область лица
        face_region = face_detector.extract_face_region(image, face_box)
        if face_region is None:
            print('❌ Не удалось извлечь область лица')
            return False

        print(f'✅ Область лица извлечена: {face_region.shape[1]}x{face_region.shape[0]}')

        # Создаем эмбеддинг
        print('🧮 Создание эмбеддинга...')
        embedding = face_recognizer.encode_face(face_region)

        if embedding is None:
            print('❌ Не удалось создать эмбеддинг')
            return False

        print(f'✅ Эмбеддинг создан: размерность {embedding.shape}')

        # Добавляем в базу данных
        print(f'\n💾 Добавление в базу данных...')
        database = FaceDatabase(database_path=database_path)

        success = database.add_face(
            person_id=person_id,
            name=name,
            embedding=embedding
        )

        if success:
            print(f'{"="*60}')
            print('✅ Лицо успешно добавлено в базу данных!')
            print(f'📁 База данных: {database.database_path}')
            print(f'👤 ID: {person_id}')
            print(f'👤 Имя: {name}')
            print(f'\nТеперь робот будет распознавать это лицо!')
            print(f'{"="*60}\n')
            return True
        else:
            print('❌ Ошибка добавления в базу данных')
            return False

    except Exception as e:
        print(f'\n❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()
        return False


def add_face_from_camera(
    person_id: str,
    name: str,
    database_path: str = '~/.watchdog_faces',
    camera_id: int = 0,
    count: int = 5
):
    """Добавляет лицо из камеры (делает несколько снимков).

    Args:
        person_id: Уникальный ID человека
        name: Имя человека
        database_path: Путь к базе данных
        camera_id: ID камеры
        count: Количество снимков для усреднения
    """
    print(f'\n{"="*60}')
    print('Добавление лица из камеры')
    print(f'{"="*60}')
    print(f'ID: {person_id}')
    print(f'Имя: {name}')
    print(f'Количество снимков: {count}')
    print(f'\nСмотрите в камеру. Нажмите Enter для начала...')
    input()

    try:
        import cv2

        # Открываем камеру
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f'❌ Не удалось открыть камеру {camera_id}')
            return False

        print('📷 Камера открыта')
        print(f'Нажмите пробел для снимка, q для выхода')

        # Инициализируем детектор и распознаватель
        face_detector = FaceDetector(method='face_recognition')
        face_recognizer = FaceRecognizer(method='face_recognition')
        database = FaceDatabase(database_path=database_path)

        embeddings = []

        frame_count = 0
        captured = 0

        print(f'\nГотовы? Нажмите пробел для каждого снимка ({count} штук)')
        print('Отображается предпросмотр - нажмите пробел когда будете готовы к снимку')

        while captured < count:
            ret, frame = cap.read()
            if not ret:
                break

            # Отображаем кадр
            display_frame = frame.copy()

            # Показываем прогресс
            cv2.putText(
                display_frame,
                f'Снимков: {captured}/{count}',
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )
            cv2.putText(
                display_frame,
                'Пробел - снимок, Q - выход',
                (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2
            )

            # Пытаемся найти лицо для предпросмотра
            face_boxes = face_detector.detect_faces(frame)
            if face_boxes:
                x, y, w, h = face_boxes[0]
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    display_frame,
                    'Лицо обнаружено',
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            cv2.imshow('Face Capture', display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord(' '):  # Пробел для снимка
                if face_boxes:
                    face_box = face_boxes[0]
                    face_region = face_detector.extract_face_region(frame, face_box)
                    if face_region is not None:
                        embedding = face_recognizer.encode_face(face_region)
                        if embedding is not None:
                            embeddings.append(embedding)
                            captured += 1
                            print(f'✅ Снимок {captured}/{count} сделан')
                        else:
                            print('⚠️  Не удалось создать эмбеддинг, попробуйте еще раз')
                    else:
                        print('⚠️  Не удалось извлечь лицо, попробуйте еще раз')
                else:
                    print('⚠️  Лицо не обнаружено, попробуйте еще раз')

            elif key == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if len(embeddings) == 0:
            print('❌ Не удалось создать ни одного эмбеддинга')
            return False

        # Добавляем все эмбеддинги в базу
        print(f'\n💾 Добавление {len(embeddings)} эмбеддингов в базу...')
        for i, embedding in enumerate(embeddings):
            database.add_face(person_id=person_id, name=name, embedding=embedding)

        print(f'{"="*60}')
        print(f'✅ Лицо успешно добавлено в базу данных!')
        print(f'📁 База данных: {database.database_path}')
        print(f'👤 ID: {person_id}')
        print(f'👤 Имя: {name}')
        print(f'📸 Снимков: {len(embeddings)}')
        print(f'\nТеперь робот будет распознавать это лицо!')
        print(f'{"="*60}\n')

        return True

    except Exception as e:
        print(f'\n❌ Ошибка: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    """Точка входа."""
    parser = argparse.ArgumentParser(
        description='Добавление лица в базу данных',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Из изображения
  ros2 run watchdog_face_detection add_face_to_db \\
    --image ~/my_photo.jpg \\
    --id owner \\
    --name "Мое Имя"

  # Из камеры (интерактивно)
  ros2 run watchdog_face_detection add_face_to_db \\
    --camera \\
    --id owner \\
    --name "Мое Имя" \\
    --count 5
        """
    )

    parser.add_argument(
        '--image',
        type=str,
        help='Путь к изображению с лицом'
    )

    parser.add_argument(
        '--camera',
        action='store_true',
        help='Использовать камеру для захвата'
    )

    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='Уникальный ID человека'
    )

    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Имя человека'
    )

    parser.add_argument(
        '--database-path',
        type=str,
        default='~/.watchdog_faces',
        help='Путь к базе данных (по умолчанию: ~/.watchdog_faces)'
    )

    parser.add_argument(
        '--camera-id',
        type=int,
        default=0,
        help='ID камеры (по умолчанию: 0)'
    )

    parser.add_argument(
        '--count',
        type=int,
        default=5,
        help='Количество снимков для усреднения (по умолчанию: 5)'
    )

    parser.add_argument(
        '--detection-method',
        type=str,
        default='face_recognition',
        choices=['haar', 'dlib', 'face_recognition'],
        help='Метод детекции (по умолчанию: face_recognition)'
    )

    parser.add_argument(
        '--recognition-method',
        type=str,
        default='face_recognition',
        choices=['face_recognition', 'insightface'],
        help='Метод распознавания (по умолчанию: face_recognition)'
    )

    args = parser.parse_args()

    if args.camera:
        success = add_face_from_camera(
            person_id=args.id,
            name=args.name,
            database_path=args.database_path,
            camera_id=args.camera_id,
            count=args.count
        )
    elif args.image:
        success = add_face_from_image(
            image_path=args.image,
            person_id=args.id,
            name=args.name,
            database_path=args.database_path,
            detection_method=args.detection_method,
            recognition_method=args.recognition_method
        )
    else:
        parser.print_help()
        sys.exit(1)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

