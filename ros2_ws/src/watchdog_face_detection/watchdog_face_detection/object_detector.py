"""Модуль детекции объектов с помощью YOLO.

Поддерживает YOLOv8 через библиотеку ultralytics.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from rclpy.logging import get_logger


class YOLODetector:
    """Класс для детекции объектов на изображениях с помощью YOLO."""

    def __init__(
        self,
        model_size: str = 'n',
        model_path: Optional[str] = None,
        confidence_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        classes: Optional[List[int]] = None
    ):
        """Инициализирует детектор YOLO.

        Args:
            model_size: Размер модели ('n', 's', 'm', 'l', 'x') - nano, small, medium, large, xlarge
            model_path: Путь к кастомной модели (если None, используется предобученная)
            confidence_threshold: Порог уверенности (0.0-1.0)
            iou_threshold: Порог IoU для NMS (0.0-1.0)
            device: Устройство для инференса ('cpu', 'cuda', '0', '1', ...)
            classes: Список классов для детекции (None = все классы)
        """
        self.model_size = model_size.lower()
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.classes = classes
        self.logger = get_logger('YOLODetector')
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """Инициализирует модель YOLO."""
        try:
            from ultralytics import YOLO

            if self.model_path:
                # Загружаем кастомную модель
                self.model = YOLO(self.model_path)
                self.logger.info(f'YOLO модель загружена из {self.model_path}')
            else:
                # Используем предобученную модель
                model_name = f'yolov8{self.model_size}.pt'
                self.model = YOLO(model_name)
                self.logger.info(f'YOLO модель {model_name} загружена')

            # Настраиваем устройство
            if self.device:
                self.model.to(self.device)
            else:
                # Автоматический выбор устройства
                try:
                    import torch
                    if torch.cuda.is_available():
                        self.model.to('cuda')
                        self.logger.info('Используется GPU (CUDA)')
                    else:
                        self.model.to('cpu')
                        self.logger.info('Используется CPU')
                except ImportError:
                    self.model.to('cpu')
                    self.logger.info('Используется CPU (PyTorch не найден)')

        except ImportError:
            self.logger.error(
                'Библиотека ultralytics не установлена. '
                'Установите: pip install ultralytics'
            )
            raise
        except Exception as e:
            self.logger.error(f'Ошибка инициализации YOLO модели: {e}')
            raise

    def detect(
        self,
        image: np.ndarray,
        return_image: bool = False
    ) -> List[Dict]:
        """Обнаруживает объекты на изображении.

        Args:
            image: Изображение в формате numpy array (BGR)
            return_image: Возвращать ли изображение с нарисованными детекциями

        Returns:
            Список словарей с информацией об обнаруженных объектах:
            [
                {
                    'class_id': int,
                    'class_name': str,
                    'confidence': float,
                    'bbox': (x, y, width, height),
                    'center': (x, y)
                },
                ...
            ]
            Если return_image=True, возвращает кортеж (detections, annotated_image)
        """
        if self.model is None:
            self.logger.warn('Модель не инициализирована')
            return [] if not return_image else ([], image)

        try:
            # YOLO ожидает RGB изображение
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 else image

            # Выполняем детекцию
            results = self.model.predict(
                rgb_image,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                classes=self.classes,
                verbose=False
            )

            detections = []
            annotated_image = image.copy() if return_image else None

            # Обрабатываем результаты
            for result in results:
                boxes = result.boxes

                for box in boxes:
                    # Получаем координаты bounding box
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    x = int(x1)
                    y = int(y1)
                    width = int(x2 - x1)
                    height = int(y2 - y1)

                    # Получаем класс и уверенность
                    class_id = int(box.cls[0].cpu().numpy())
                    confidence = float(box.conf[0].cpu().numpy())
                    class_name = self.model.names[class_id]

                    detection = {
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': (x, y, width, height),
                        'center': (x + width // 2, y + height // 2)
                    }
                    detections.append(detection)

                    # Рисуем на изображении, если нужно
                    if return_image and annotated_image is not None:
                        cv2.rectangle(
                            annotated_image,
                            (x, y),
                            (x + width, y + height),
                            (0, 255, 0),
                            2
                        )
                        label = f'{class_name} {confidence:.2f}'
                        cv2.putText(
                            annotated_image,
                            label,
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.5,
                            (0, 255, 0),
                            2
                        )

            if return_image:
                return detections, annotated_image
            return detections

        except Exception as e:
            self.logger.error(f'Ошибка детекции объектов: {e}')
            import traceback
            traceback.print_exc()
            return [] if not return_image else ([], image)

    def detect_classes(
        self,
        image: np.ndarray,
        target_classes: List[str]
    ) -> List[Dict]:
        """Обнаруживает только указанные классы объектов.

        Args:
            image: Изображение в формате numpy array (BGR)
            target_classes: Список названий классов для детекции (например, ['person', 'car'])

        Returns:
            Список словарей с информацией об обнаруженных объектах
        """
        if self.model is None:
            return []

        # Преобразуем названия классов в ID
        class_ids = []
        for class_name in target_classes:
            for class_id, name in self.model.names.items():
                if name.lower() == class_name.lower():
                    class_ids.append(class_id)
                    break

        if not class_ids:
            self.logger.warn(f'Классы {target_classes} не найдены в модели')
            return []

        # Сохраняем текущие классы и временно устанавливаем нужные
        original_classes = self.classes
        self.classes = class_ids

        try:
            detections = self.detect(image)
        finally:
            # Восстанавливаем оригинальные классы
            self.classes = original_classes

        return detections

    def get_class_names(self) -> Dict[int, str]:
        """Возвращает словарь соответствия ID классов их названиям.

        Returns:
            Словарь {class_id: class_name}
        """
        if self.model is None:
            return {}
        return self.model.names.copy()
