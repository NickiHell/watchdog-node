"""ROS2 узел для детекции и распознавания лиц."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from geometry_msgs.msg import Point, Twist
import cv2
import numpy as np
from typing import List, Optional

try:
    from cv_bridge import CvBridge
except ImportError:
    # Fallback для случаев когда cv_bridge не установлен
    CvBridge = None

from watchdog_face_detection.face_detector import FaceDetector
from watchdog_face_detection.face_recognizer import FaceRecognizer
from watchdog_face_detection.face_database import FaceDatabase
from watchdog_face_detection.target_tracker import TargetTracker


class FaceDetectionMessage:
    """Сообщение с информацией о распознанном лице."""

    def __init__(self, person_id: str, name: str, confidence: float, bbox: tuple):
        self.person_id = person_id
        self.name = name
        self.confidence = confidence
        self.bbox = bbox  # (x, y, width, height)


class FaceDetectionNode(Node):
    """ROS2 узел для детекции и распознавания лиц."""

    def __init__(self):
        super().__init__('face_detection_node')

        # Параметры
        self.declare_parameter('detection.method', 'face_recognition')
        self.declare_parameter('detection.model_path', '')
        self.declare_parameter('recognition.method', 'face_recognition')
        self.declare_parameter('database.path', '~/.watchdog_faces')
        self.declare_parameter('recognition.threshold', 0.6)
        self.declare_parameter('camera.topic', '/camera/image_raw')
        self.declare_parameter('processing.frame_skip', 5)  # Обрабатывать каждый N-й кадр
        self.declare_parameter('tracking.enabled', True)
        self.declare_parameter('tracking.tracker_type', 'CSRT')
        self.declare_parameter('tracking.target_person_id', '')  # ID цели для отслеживания (пусто = любое лицо)

        # Инициализация компонентов
        if CvBridge is None:
            self.get_logger().error('cv_bridge не установлен. Установите: sudo apt install ros-humble-cv-bridge')
            raise ImportError('cv_bridge required')
        self.bridge = CvBridge()

        detection_method = self.get_parameter('detection.method').get_parameter_value().string_value
        detection_model_path = self.get_parameter('detection.model_path').get_parameter_value().string_value

        try:
            self.face_detector = FaceDetector(
                method=detection_method,
                model_path=detection_model_path if detection_model_path else None
            )
        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации детектора: {e}')
            self.face_detector = None

        recognition_method = self.get_parameter('recognition.method').get_parameter_value().string_value

        try:
            self.face_recognizer = FaceRecognizer(method=recognition_method)
        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации распознавателя: {e}')
            self.face_recognizer = None

        database_path = self.get_parameter('database.path').get_parameter_value().string_value

        try:
            self.face_database = FaceDatabase(database_path=database_path)
        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации базы данных: {e}')
            self.face_database = None

        # Переменные состояния
        self.frame_counter = 0
        self.frame_skip = self.get_parameter('processing.frame_skip').get_parameter_value().integer_value
        self.recognition_threshold = self.get_parameter('recognition.threshold').get_parameter_value().double_value

        # Инициализация трекера
        tracking_enabled = self.get_parameter('tracking.enabled').get_parameter_value().bool_value
        tracker_type = self.get_parameter('tracking.tracker_type').get_parameter_value().string_value
        self.target_tracker = TargetTracker(tracker_type=tracker_type) if tracking_enabled else None
        self.tracking_enabled = tracking_enabled
        self.target_person_id = self.get_parameter('tracking.target_person_id').get_parameter_value().string_value
        self.last_frame = None

        # Издатели
        self.detections_pub = self.create_publisher(String, '/face_detection/detections', 10)
        self.authorized_pub = self.create_publisher(String, '/face_detection/authorized', 10)
        self.unknown_pub = self.create_publisher(String, '/face_detection/unknown', 10)
        self.tracking_cmd_pub = self.create_publisher(Twist, '/face_detection/tracking_cmd', 10)
        self.target_position_pub = self.create_publisher(Point, '/face_detection/target_position', 10)

        # Подписчики
        camera_topic = self.get_parameter('camera.topic').get_parameter_value().string_value
        self.camera_sub = self.create_subscription(
            Image,
            camera_topic,
            self.camera_callback,
            10
        )

        self.get_logger().info(f'Face detection node запущен, подписан на {camera_topic}')

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

        if not self.face_detector or not self.face_recognizer or not self.face_database:
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

            # Обнаруживаем лица
            face_boxes = self.face_detector.detect_faces(cv_image)

            if not face_boxes:
                return

            detections = []

            # Обрабатываем каждое обнаруженное лицо
            for face_box in face_boxes:
                # Извлекаем область лица
                face_region = self.face_detector.extract_face_region(cv_image, face_box)

                if face_region is None:
                    continue

                # Создаем эмбеддинг
                embedding = self.face_recognizer.encode_face(face_region)

                if embedding is None:
                    continue

                # Ищем лицо в базе данных
                match = self.face_database.find_face(embedding, threshold=self.recognition_threshold)

                if match:
                    person_id, name, distance = match
                    confidence = 1.0 - (distance / self.recognition_threshold)  # Нормализуем в 0-1

                    detection = FaceDetectionMessage(person_id, name, confidence, face_box)
                    detections.append(detection)

                    # Публикуем информацию об авторизованном лице
                    auth_msg = String()
                    auth_msg.data = f'{person_id}:{name}:{confidence:.3f}'
                    self.authorized_pub.publish(auth_msg)

                    self.get_logger().info(f'Распознано лицо: {name} (confidence={confidence:.3f})')

                    # Если трекинг включен и это целевое лицо (или не указано конкретное)
                    if self.tracking_enabled and self.target_tracker:
                        should_track = (
                            not self.target_person_id or  # Не указана конкретная цель
                            person_id == self.target_person_id  # Или это целевое лицо
                        )

                        if should_track and not self.target_tracker.is_tracking:
                            # Начинаем отслеживание этого лица
                            bbox = (face_box[0], face_box[1], face_box[2], face_box[3])
                            if self.target_tracker.init_tracker(cv_image, bbox, person_id):
                                self.get_logger().info(f'Начато отслеживание цели: {name} (ID: {person_id})')

                else:
                    # Неизвестное лицо
                    detection = FaceDetectionMessage('unknown', 'Unknown', 0.0, face_box)
                    detections.append(detection)

                    unknown_msg = String()
                    unknown_msg.data = 'unknown'
                    self.unknown_pub.publish(unknown_msg)

                    self.get_logger().debug('Обнаружено неизвестное лицо')

            # Публикуем все детекции
            if detections:
                detections_str = ','.join([
                    f'{d.person_id}:{d.name}:{d.confidence:.3f}:{d.bbox[0]}:{d.bbox[1]}:{d.bbox[2]}:{d.bbox[3]}'
                    for d in detections
                ])
                detections_msg = String()
                detections_msg.data = detections_str
                self.detections_pub.publish(detections_msg)

        except Exception as e:
            self.get_logger().error(f'Ошибка обработки изображения: {e}')
            import traceback
            traceback.print_exc()


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = FaceDetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
