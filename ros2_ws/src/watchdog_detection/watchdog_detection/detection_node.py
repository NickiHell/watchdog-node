"""ROS2 узел детекции объектов: YOLOv8n + ByteTrack.

Паттерн "Detection + Tracking":
  - YOLOv8n запускается каждые YOLO_SKIP кадров (~80 мс на RPI 5 CPU)
  - ByteTrack.update() вызывается при детекции, predict() — каждый кадр
  - Результат: плавные треки 30 FPS при 10 FPS детекции

Публикует /detection/tracks (watchdog_msgs/DetectionArray) для watchdog_gimbal.
"""

import time

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String

try:
    from ultralytics import YOLO
    from boxmot import ByteTrack

    DETECTION_AVAILABLE = True
except ImportError:
    DETECTION_AVAILABLE = False

try:
    from watchdog_msgs.msg import DetectionArray, Detection

    CUSTOM_MSGS = True
except ImportError:
    CUSTOM_MSGS = False


class DetectionNode(Node):
    """YOLOv8n детекция + ByteTrack трекинг объектов."""

    # COCO классы которые отслеживаем
    TRACKED_CLASSES = {
        0: "person",
        2: "car",
        3: "motorcycle",
        5: "bus",
        7: "truck",
    }

    def __init__(self):
        super().__init__("detection_node")

        self.declare_parameter("model", "yolov8n.pt")
        self.declare_parameter("confidence", 0.45)
        self.declare_parameter("iou", 0.5)
        self.declare_parameter("imgsz", 640)
        self.declare_parameter("device", "cpu")
        self.declare_parameter("yolo_skip_frames", 3)
        self.declare_parameter("classes", [0, 2, 3, 5, 7])

        self.model_path = self.get_parameter("model").value
        self.conf = self.get_parameter("confidence").value
        self.iou = self.get_parameter("iou").value
        self.imgsz = self.get_parameter("imgsz").value
        self.device = self.get_parameter("device").value
        self.yolo_skip = self.get_parameter("yolo_skip_frames").value
        self.classes = list(self.get_parameter("classes").value)

        self.bridge = CvBridge()
        self.frame_count = 0
        self.yolo = None  # type: ignore[var-annotated]
        self.tracker = None  # type: ignore[var-annotated]
        self.last_detections = np.empty((0, 6))  # [x1,y1,x2,y2,conf,cls]

        if not DETECTION_AVAILABLE:
            self.get_logger().error("ultralytics или boxmot не установлены. Установите: pip install ultralytics boxmot")
        else:
            self._init_models()

        # Подписчики
        self.image_sub = self.create_subscription(Image, "/camera/image_raw", self._image_callback, 5)

        # Издатели
        if CUSTOM_MSGS:
            self.tracks_pub = self.create_publisher(DetectionArray, "/detection/tracks", 10)
        self.status_pub = self.create_publisher(String, "/detection/status", 10)

        # Публикация отладочного видео (опционально)
        self.debug_pub = self.create_publisher(Image, "/detection/debug_image", 1)

        self.get_logger().info(
            f"DetectionNode запущен | YOLO: {self.model_path} | "
            f"ByteTrack | skip={self.yolo_skip} | device={self.device}"
        )

    def _init_models(self):
        """Инициализирует YOLOv8n и ByteTrack."""
        try:
            self.get_logger().info(f"Загружаем {self.model_path}...")
            self.yolo = YOLO(self.model_path)
            # Прогрев модели
            dummy = np.zeros((self.imgsz, self.imgsz, 3), dtype=np.uint8)
            self.yolo.predict(dummy, verbose=False, device=self.device)
            self.get_logger().info("YOLOv8n загружен и прогрет")
        except Exception as e:
            self.get_logger().error(f"Ошибка загрузки YOLO: {e}")
            self.yolo = None

        try:
            self.tracker = ByteTrack(
                track_thresh=0.45,
                track_buffer=30,
                match_thresh=0.8,
                frame_rate=30,
            )
            self.get_logger().info("ByteTrack инициализирован")
        except Exception as e:
            self.get_logger().error(f"Ошибка инициализации ByteTrack: {e}")
            self.tracker = None

    def _image_callback(self, msg: Image):
        if not DETECTION_AVAILABLE or self.yolo is None or self.tracker is None:
            return

        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().debug(f"cv_bridge ошибка: {e}")
            return

        self.frame_count += 1
        t0 = time.monotonic()

        # Запускаем YOLO каждые yolo_skip кадров
        if self.frame_count % self.yolo_skip == 0:
            self.last_detections = self._run_yolo(frame)
            tracks = self.tracker.update(self.last_detections, frame)  # type: ignore[union-attr]
        else:
            # Только predict (ByteTrack интерполирует)
            if len(self.last_detections) == 0:
                return
            tracks = self.tracker.update(np.empty((0, 6)), frame)  # type: ignore[union-attr]

        dt = (time.monotonic() - t0) * 1000

        if tracks is not None and len(tracks) > 0:
            self._publish_tracks(tracks, msg.header)
            self._publish_debug(frame, tracks)

        status = String()
        status.data = (
            f"frame={self.frame_count}|tracks={len(tracks) if tracks is not None else 0}"
            f"|dt={dt:.1f}ms|yolo={'yes' if self.frame_count % self.yolo_skip == 0 else 'no'}"
        )
        self.status_pub.publish(status)

    def _run_yolo(self, frame: np.ndarray) -> np.ndarray:
        """Запускает YOLOv8n и возвращает [x1,y1,x2,y2,conf,cls]."""
        try:
            results = self.yolo.predict(  # type: ignore[union-attr]
                frame,
                conf=self.conf,
                iou=self.iou,
                imgsz=self.imgsz,
                classes=self.classes,
                device=self.device,
                verbose=False,
            )
            if not results or results[0].boxes is None:
                return np.empty((0, 6))

            boxes = results[0].boxes
            if len(boxes) == 0:
                return np.empty((0, 6))

            xyxy = boxes.xyxy.cpu().numpy()
            conf = boxes.conf.cpu().numpy().reshape(-1, 1)
            cls = boxes.cls.cpu().numpy().reshape(-1, 1)
            return np.hstack([xyxy, conf, cls])

        except Exception as e:
            self.get_logger().debug(f"YOLO ошибка: {e}")
            return np.empty((0, 6))

    def _publish_tracks(self, tracks: np.ndarray, header):
        """Публикует треки в /detection/tracks."""
        if not CUSTOM_MSGS:
            return

        try:
            msg = DetectionArray()
            msg.header = header

            for track in tracks:
                # ByteTrack формат: [x1,y1,x2,y2,track_id,conf,cls,...]
                if len(track) < 7:
                    continue
                x1, y1, x2, y2 = track[0:4]
                track_id = int(track[4])
                conf = float(track[5])
                cls_id = int(track[6]) if len(track) > 6 else 0

                det = Detection()
                det.track_id = track_id
                det.class_id = cls_id
                det.class_name = self.TRACKED_CLASSES.get(cls_id, "unknown")
                det.confidence = conf
                det.x1 = float(x1)
                det.y1 = float(y1)
                det.x2 = float(x2)
                det.y2 = float(y2)
                det.cx = float((x1 + x2) / 2)
                det.cy = float((y1 + y2) / 2)
                det.width = float(x2 - x1)
                det.height = float(y2 - y1)

                msg.detections.append(det)

            self.tracks_pub.publish(msg)

        except Exception as e:
            self.get_logger().debug(f"Ошибка публикации треков: {e}")

    def _publish_debug(self, frame: np.ndarray, tracks: np.ndarray):
        """Публикует отладочный кадр с рамками треков."""
        if self.debug_pub.get_subscription_count() == 0:
            return

        try:
            vis = frame.copy()
            for track in tracks:
                if len(track) < 5:
                    continue
                x1, y1, x2, y2 = int(track[0]), int(track[1]), int(track[2]), int(track[3])
                tid = int(track[4])
                cls_id = int(track[6]) if len(track) > 6 else 0
                label = f"{self.TRACKED_CLASSES.get(cls_id, '?')} #{tid}"
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(vis, label, (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            debug_msg = self.bridge.cv2_to_imgmsg(vis, encoding="bgr8")
            self.debug_pub.publish(debug_msg)

        except Exception as e:
            self.get_logger().debug(f"Debug publish ошибка: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = DetectionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
