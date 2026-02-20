"""ROS2 узел для захвата и публикации изображений с камеры."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo

try:
    from cv_bridge import CvBridge
except ImportError:
    CvBridge = None

from watchdog_camera.camera_driver import CameraDriver, USBCameraDriver, PiCameraDriver, MultiCameraDriver


class CameraNode(Node):
    """ROS2 узел для работы с камерой."""

    def __init__(self):
        super().__init__("camera_node")

        # Параметры
        self.declare_parameter("camera.type", "usb")  # usb, picamera, multi
        self.declare_parameter("camera.device_id", 0)
        self.declare_parameter("camera.device_ids", [0])  # Для multi
        self.declare_parameter("camera.width", 1920)
        self.declare_parameter("camera.height", 1080)
        self.declare_parameter("camera.fps", 30)
        self.declare_parameter("camera.frame_id", "camera_frame")
        self.declare_parameter("camera.topic", "/camera/image_raw")
        self.declare_parameter("camera.stitch_panorama", False)  # Для multi камер

        # Инициализация компонентов
        if CvBridge is None:
            self.get_logger().error("cv_bridge не установлен. Установите: sudo apt install ros-humble-cv-bridge")
            raise ImportError("cv_bridge required")
        self.bridge = CvBridge()

        # Инициализация драйвера камеры
        camera_type = self.get_parameter("camera.type").get_parameter_value().string_value
        device_id = self.get_parameter("camera.device_id").get_parameter_value().integer_value
        width = self.get_parameter("camera.width").get_parameter_value().integer_value
        height = self.get_parameter("camera.height").get_parameter_value().integer_value
        fps = self.get_parameter("camera.fps").get_parameter_value().integer_value

        self.camera: CameraDriver | None = None
        self._initialize_camera(camera_type, device_id, width, height, fps)

        # Издатели
        camera_topic = self.get_parameter("camera.topic").get_parameter_value().string_value
        self.image_pub = self.create_publisher(Image, camera_topic, 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, "/camera/camera_info", 10)

        # Таймер для публикации кадров
        self.create_timer(1.0 / fps, self.capture_timer_callback)

        # Таймер для информации о камере
        self.create_timer(5.0, self.info_timer_callback)

        if self.camera and self.camera.is_opened:
            self.get_logger().info("Camera node запущен")
            self.publish_camera_info()
        else:
            self.get_logger().error("Не удалось инициализировать камеру")

    def _initialize_camera(self, camera_type: str, device_id: int, width: int, height: int, fps: int):
        """Инициализирует драйвер камеры."""
        try:
            if camera_type == "usb":
                self.camera = USBCameraDriver(device_id, width, height, fps)
            elif camera_type == "picamera":
                self.camera = PiCameraDriver(width, height, fps)
            elif camera_type == "multi":
                device_ids = self.get_parameter("camera.device_ids").get_parameter_value().integer_array_value
                if not device_ids:
                    device_ids = [0, 1]  # По умолчанию две камеры
                self.camera = MultiCameraDriver(device_ids, width, height, fps)
            else:
                self.get_logger().error(f"Неизвестный тип камеры: {camera_type}")
                return

            if self.camera.open():
                self.get_logger().info(f"Камера типа {camera_type} инициализирована")
            else:
                self.get_logger().error(f"Не удалось открыть камеру типа {camera_type}")

        except Exception as e:
            self.get_logger().error(f"Ошибка инициализации камеры: {e}")
            import traceback

            traceback.print_exc()

    def capture_timer_callback(self):
        """Таймер для захвата и публикации кадров."""
        if not self.camera or not self.camera.is_opened:
            return

        try:
            # Читаем кадр
            if isinstance(self.camera, MultiCameraDriver):
                stitch = self.get_parameter("camera.stitch_panorama").get_parameter_value().bool_value
                if stitch:
                    frame = self.camera.read_stitched()
                else:
                    # Публикуем только первую камеру
                    frames = self.camera.read_all()
                    frame = frames[0] if frames else None
            else:
                frame = self.camera.read()

            if frame is None:
                return

            # Конвертируем в ROS2 сообщение
            frame_id = self.get_parameter("camera.frame_id").get_parameter_value().string_value
            image_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            image_msg.header.frame_id = frame_id
            image_msg.header.stamp = self.get_clock().now().to_msg()

            # Публикуем
            self.image_pub.publish(image_msg)

        except Exception as e:
            self.get_logger().error(f"Ошибка захвата кадра: {e}")

    def publish_camera_info(self):
        """Публикует информацию о камере."""
        if not self.camera:
            return

        try:
            info = self.camera.get_info()
            if not info:
                return

            camera_info = CameraInfo()
            camera_info.header.frame_id = self.get_parameter("camera.frame_id").get_parameter_value().string_value
            camera_info.header.stamp = self.get_clock().now().to_msg()

            if isinstance(info, list):
                # Для нескольких камер берем информацию первой
                if len(info) > 0:
                    info = info[0]
                else:
                    return

            camera_info.width = info.get("width", 0)
            camera_info.height = info.get("height", 0)

            # Простая калибровка (можно заменить на реальную)
            camera_info.distortion_model = "plumb_bob"
            camera_info.D = [0.0, 0.0, 0.0, 0.0, 0.0]  # Коэффициенты искажения

            # Матрица камеры (упрощенная, для реального использования нужна калибровка)
            fx = fy = info.get("width", 1920) * 0.7  # Приблизительно
            cx = info.get("width", 1920) / 2.0
            cy = info.get("height", 1080) / 2.0

            camera_info.K = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]

            camera_info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]

            camera_info.P = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]

            self.camera_info_pub.publish(camera_info)

        except Exception as e:
            self.get_logger().error(f"Ошибка публикации camera_info: {e}")

    def info_timer_callback(self):
        """Таймер для периодической публикации информации."""
        self.publish_camera_info()

    def destroy_node(self):
        """Очистка при завершении узла."""
        if self.camera:
            self.camera.close()
        super().destroy_node()


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = CameraNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
