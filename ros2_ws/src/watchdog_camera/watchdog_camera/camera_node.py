"""ROS2 узел для захвата и публикации изображений с камеры SIYI A8 mini."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo

try:
    from cv_bridge import CvBridge
except ImportError:
    CvBridge = None

from watchdog_camera.camera_driver import SIYIDriver


class CameraNode(Node):
    """ROS2 узел для работы с камерой SIYI A8 mini (RTSP)."""

    def __init__(self):
        super().__init__("camera_node")

        # Параметры камеры и SIYI (из config: camera.frame_id, camera.topic, camera.siyi.*)
        self.declare_parameter("camera.siyi.ip", "192.168.144.25")
        self.declare_parameter("camera.siyi.stream_port", 8554)
        self.declare_parameter("camera.width", 1920)
        self.declare_parameter("camera.height", 1080)
        self.declare_parameter("camera.fps", 30)
        self.declare_parameter("camera.frame_id", "camera_frame")
        self.declare_parameter("camera.topic", "/camera/image_raw")

        if CvBridge is None:
            self.get_logger().error("cv_bridge не установлен. Установите: sudo apt install ros-humble-cv-bridge")
            raise ImportError("cv_bridge required")
        self.bridge = CvBridge()

        siyi_ip = self.get_parameter("camera.siyi.ip").get_parameter_value().string_value
        siyi_stream_port = self.get_parameter("camera.siyi.stream_port").get_parameter_value().integer_value
        width = self.get_parameter("camera.width").get_parameter_value().integer_value
        height = self.get_parameter("camera.height").get_parameter_value().integer_value
        fps = self.get_parameter("camera.fps").get_parameter_value().integer_value

        self.camera = SIYIDriver(ip=siyi_ip, stream_port=siyi_stream_port, width=width, height=height, fps=fps)

        if not self.camera.open():
            self.get_logger().error("Не удалось открыть камеру SIYI")
            self.camera = None

        camera_topic = self.get_parameter("camera.topic").get_parameter_value().string_value
        self.image_pub = self.create_publisher(Image, camera_topic, 10)
        self.camera_info_pub = self.create_publisher(CameraInfo, "/camera/camera_info", 10)

        self.create_timer(1.0 / fps, self.capture_timer_callback)
        self.create_timer(5.0, self.info_timer_callback)

        if self.camera and self.camera.is_opened:
            self.get_logger().info("Camera node запущен (SIYI A8 mini)")
            self.publish_camera_info()
        else:
            self.get_logger().error("Не удалось инициализировать камеру SIYI")

    def capture_timer_callback(self):
        """Таймер для захвата и публикации кадров."""
        if not self.camera or not self.camera.is_opened:
            return

        try:
            frame = self.camera.read()
            if frame is None:
                return

            frame_id = self.get_parameter("camera.frame_id").get_parameter_value().string_value
            image_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            image_msg.header.frame_id = frame_id
            image_msg.header.stamp = self.get_clock().now().to_msg()
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
            camera_info.width = info.get("width", 0)
            camera_info.height = info.get("height", 0)
            camera_info.distortion_model = "plumb_bob"
            camera_info.D = [0.0, 0.0, 0.0, 0.0, 0.0]
            fx = fy = info.get("width", 1920) * 0.7
            cx = info.get("width", 1920) / 2.0
            cy = info.get("height", 1080) / 2.0
            camera_info.K = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]
            camera_info.R = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
            camera_info.P = [fx, 0.0, cx, 0.0, 0.0, fy, cy, 0.0, 0.0, 0.0, 1.0, 0.0]
            self.camera_info_pub.publish(camera_info)

        except Exception as e:
            self.get_logger().error(f"Ошибка публикации camera_info: {e}")

    def info_timer_callback(self):
        """Периодическая публикация camera_info."""
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
