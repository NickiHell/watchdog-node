"""ROS2 узел для детекции объектов с помощью YOLO."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import Point, Twist
import cv2
import numpy as np
from typing import List, Optional
import json

try:
    from cv_bridge import CvBridge
except ImportError:
    CvBridge = None

from watchdog_face_detection.object_detector import YOLODetector
from watchdog_face_detection.target_tracker import TargetTracker


class ObjectDetectionNode(Node):
    """ROS2 узел для детекции объектов с помощью YOLO."""

    def __init__(self):
        super().__init__('object_detection_node')

        # Параметры
        self.declare_parameter('yolo.model_size', 'n')  # n, s, m, l, x
        self.declare_parameter('yolo.model_path', '')
        self.declare_parameter('yolo.confidence_threshold', 0.25)
        self.declare_parameter('yolo.iou_threshold', 0.45)
        self.declare_parameter('yolo.device', '')  # Пусто = автоопределение
        self.declare_parameter('yolo.classes', [])  # Список классов для детекции (пусто = все)
        self.declare_parameter('yolo.target_classes', ['person'])  # Классы для отслеживания
        self.declare_parameter('camera.topic', '/camera/image_raw')
        self.declare_parameter('processing.frame_skip', 5)
        self.declare_parameter('tracking.enabled', True)
        self.declare_parameter('tracking.tracker_type', 'CSRT')
        self.declare_parameter('tracking.target_class', 'person')  # Класс для отслеживания

        # Инициализация компонентов
        if CvBridge is None:
            self.get_logger().error('cv_bridge не установлен. Установите: sudo apt install ros-humble-cv-bridge')
            raise ImportError('cv_bridge required')
        self.bridge = CvBridge()

        # Параметры YOLO
        model_size = self.get_parameter('yolo.model_size').get_parameter_value().string_value
        model_path = self.get_parameter('yolo.model_path').get_parameter_value().string_value
        confidence_threshold = self.get_parameter('yolo.confidence_threshold').get_parameter_value().double_value
        iou_threshold = self.get_parameter('yolo.iou_threshold').get_parameter_value().double_value
        device = self.get_parameter('yolo.device').get_parameter_value().string_value
        classes = self.get_parameter('yolo.classes').get_parameter_value().integer_array_value
        target_classes = self.get_parameter('yolo.target_classes').get_parameter_value().string_array_value

        try:
            self.yolo_detector = YOLODetector(
                model_size=model_size,
                model_path=model_path if model_path else None,
                confidence_threshold=confidence_threshold,
                iou_threshold=iou_threshold,
                device=device if device else None,
                classes=classes if classes else None
            )
            self.get_logger().info('YOLO детектор инициализирован')
        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации YOLO детектора: {e}')
            self.yolo_detector = None

        # Переменные состояния
        self.frame_counter = 0
        self.frame_skip = self.get_parameter('processing.frame_skip').get_parameter_value().integer_value
        self.target_classes = target_classes
        self.last_frame = None

        # Инициализация трекера
        tracking_enabled = self.get_parameter('tracking.enabled').get_parameter_value().bool_value
        tracker_type = self.get_parameter('tracking.tracker_type').get_parameter_value().string_value
        self.target_tracker = TargetTracker(tracker_type=tracker_type) if tracking_enabled else None
        self.tracking_enabled = tracking_enabled
        self.tracking_target_class = self.get_parameter('tracking.target_class').get_parameter_value().string_value

        # Издатели
        self.detections_pub = self.create_publisher(String, '/object_detection/detections', 10)
        self.target_detections_pub = self.create_publisher(String, '/object_detection/target_detections', 10)
        self.tracking_cmd_pub = self.create_publisher(Twist, '/object_detection/tracking_cmd', 10)
        self.target_position_pub = self.create_publisher(Point, '/object_detection/target_position', 10)
        self.annotated_image_pub = self.create_publisher(Image, '/object_detection/annotated_image', 10)

        # Подписчики
        camera_topic = self.get_parameter('camera.topic').get_parameter_value().string_value
        self.camera_sub = self.create_subscription(
            Image,
            camera_topic,
            self.camera_callback,
            10
        )

        self.get_logger().info(f'Object detection node запущен, подписан на {camera_topic}')

    def camera_callback(self, msg: Image):
        """Обработчик изображений с камеры.

        Args:
            msg: ROS2 сообщение с изображением
        """
        # Пропускаем кадры для снижения нагрузки
        self.frame_counter += 1
        if self.frame_counter < self.frame_skip:
            return
        self.frame_counter = 0

        if not self.yolo_detector:
            return

        try:
            # Конвертируем ROS изображение в OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            self.last_frame = cv_image

            # Если трекинг активен, обновляем позицию цели
            if self.tracking_enabled and self.target_tracker and self.target_tracker.is_tracking:
                success, bbox = self.target_tracker.update(cv_image)
                if success:
                    # Вычисляем команду для сопровождения
                    cmd = self.target_tracker.compute_tracking_command(
                        cv_image.shape[1], cv_image.shape[0]
                    )
                    if cmd:
                        twist = Twist()
                        twist.linear.x = cmd['linear_x']
                        twist.linear.y = cmd['linear_y']
                        twist.linear.z = cmd['linear_z']
                        twist.angular.z = cmd['angular_z']
                        self.tracking_cmd_pub.publish(twist)

                    # Публикуем позицию цели
                    target_pos = self.target_tracker.get_target_position_in_frame()
                    if target_pos:
                        self.target_position_pub.publish(target_pos)
                else:
                    # Цель потеряна
                    self.get_logger().warn('Цель потеряна при отслеживании')
                    self.target_tracker.stop_tracking()

            # Обнаруживаем объекты
            detections, annotated_image = self.yolo_detector.detect(cv_image, return_image=True)

            if not detections:
                return

            # Фильтруем детекции по целевым классам
            target_detections = [
                d for d in detections
                if d['class_name'].lower() in [c.lower() for c in self.target_classes]
            ]

            # Публикуем все детекции
            detections_data = {
                'detections': [
                    {
                        'class_id': d['class_id'],
                        'class_name': d['class_name'],
                        'confidence': d['confidence'],
                        'bbox': d['bbox'],
                        'center': d['center']
                    }
                    for d in detections
                ]
            }
            detections_msg = String()
            detections_msg.data = json.dumps(detections_data)
            self.detections_pub.publish(detections_msg)

            # Публикуем целевые детекции отдельно
            if target_detections:
                target_data = {
                    'detections': [
                        {
                            'class_id': d['class_id'],
                            'class_name': d['class_name'],
                            'confidence': d['confidence'],
                            'bbox': d['bbox'],
                            'center': d['center']
                        }
                        for d in target_detections
                    ]
                }
                target_msg = String()
                target_msg.data = json.dumps(target_data)
                self.target_detections_pub.publish(target_msg)

                # Если трекинг включен и есть целевой объект
                if self.tracking_enabled and self.target_tracker:
                    # Ищем объект нужного класса
                    tracking_target = None
                    for det in target_detections:
                        if det['class_name'].lower() == self.tracking_target_class.lower():
                            tracking_target = det
                            break

                    if tracking_target and not self.target_tracker.is_tracking:
                        # Начинаем отслеживание
                        bbox = tracking_target['bbox']
                        if self.target_tracker.init_tracker(cv_image, bbox, tracking_target['class_name']):
                            self.get_logger().info(
                                f'Начато отслеживание объекта: {tracking_target["class_name"]} '
                                f'(confidence={tracking_target["confidence"]:.2f})'
                            )

            # Публикуем аннотированное изображение
            if annotated_image is not None:
                try:
                    annotated_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
                    self.annotated_image_pub.publish(annotated_msg)
                except Exception as e:
                    self.get_logger().error(f'Ошибка публикации аннотированного изображения: {e}')

            # Логируем информацию
            if detections:
                self.get_logger().debug(
                    f'Обнаружено объектов: {len(detections)}, '
                    f'целевых: {len(target_detections)}'
                )

        except Exception as e:
            self.get_logger().error(f'Ошибка обработки изображения: {e}')
            import traceback
            traceback.print_exc()


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = ObjectDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
