"""ROS2 узел для работы с лидаром."""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import String
import time

from typing import Optional
from watchdog_lidar.lidar_base import LidarDriver
from watchdog_lidar.rplidar_driver import RPLidarDriver
from watchdog_lidar.generic_lidar_driver import GenericLidarDriver


class LidarNode(Node):
    """ROS2 узел для работы с лидаром."""

    def __init__(self):
        super().__init__('lidar_node')

        # Параметры
        self.declare_parameter('lidar.type', 'rplidar')  # rplidar, generic
        self.declare_parameter('lidar.port', '/dev/ttyUSB0')
        self.declare_parameter('lidar.baudrate', 115200)
        self.declare_parameter('lidar.frame_id', 'lidar_frame')
        self.declare_parameter('lidar.angle_min', -3.14159)
        self.declare_parameter('lidar.angle_max', 3.14159)
        self.declare_parameter('lidar.range_min', 0.05)
        self.declare_parameter('lidar.range_max', 12.0)
        self.declare_parameter('lidar.scan_rate', 10.0)  # Гц

        # Инициализация драйвера
        lidar_type = self.get_parameter('lidar.type').get_parameter_value().string_value
        port = self.get_parameter('lidar.port').get_parameter_value().string_value
        baudrate = self.get_parameter('lidar.baudrate').get_parameter_value().integer_value

        self.lidar: Optional[LidarDriver] = None
        self._initialize_lidar(lidar_type, port, baudrate)

        # Издатели
        self.scan_pub = self.create_publisher(LaserScan, '/sensor/lidar/scan', 10)
        self.status_pub = self.create_publisher(String, '/lidar/status', 10)

        # Таймер для публикации сканов
        scan_rate = self.get_parameter('lidar.scan_rate').get_parameter_value().double_value
        self.create_timer(1.0 / scan_rate, self.scan_timer_callback)

        # Таймер для статуса
        self.create_timer(1.0, self.status_timer_callback)

        if self.lidar:
            self.publish_status('initialized')

    def _initialize_lidar(self, lidar_type: str, port: str, baudrate: int):
        """Инициализирует драйвер лидара."""
        try:
            if lidar_type == 'rplidar':
                self.lidar = RPLidarDriver(port, baudrate)
            elif lidar_type == 'generic':
                self.lidar = GenericLidarDriver(port, baudrate)
            else:
                self.get_logger().error(f'Неизвестный тип лидара: {lidar_type}')
                return

            # Подключаемся
            if self.lidar.connect():
                # Получаем информацию
                info = self.lidar.get_info()
                if info:
                    self.get_logger().info(f'Информация о лидаре: {info}')

                # Начинаем сканирование
                if self.lidar.start_scanning():
                    self.get_logger().info('Сканирование лидара запущено')
                    self.publish_status('scanning')
                else:
                    self.get_logger().error('Не удалось запустить сканирование')
                    self.publish_status('scan_failed')
            else:
                self.get_logger().error('Не удалось подключиться к лидару')
                self.publish_status('connection_failed')

        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации лидара: {e}')
            import traceback
            traceback.print_exc()

    def scan_timer_callback(self):
        """Таймер для публикации сканов."""
        if not self.lidar or not self.lidar.is_connected:
            return

        try:
            scan = self.lidar.get_scan()
            if scan:
                # Конвертируем в LaserScan
                frame_id = self.get_parameter('lidar.frame_id').get_parameter_value().string_value
                laserscan_msg = scan.to_laserscan(frame_id)

                # Устанавливаем параметры из конфига
                laserscan_msg.angle_min = self.get_parameter('lidar.angle_min').get_parameter_value().double_value
                laserscan_msg.angle_max = self.get_parameter('lidar.angle_max').get_parameter_value().double_value
                laserscan_msg.range_min = self.get_parameter('lidar.range_min').get_parameter_value().double_value
                laserscan_msg.range_max = self.get_parameter('lidar.range_max').get_parameter_value().double_value

                laserscan_msg.header.stamp = self.get_clock().now().to_msg()

                # Публикуем
                self.scan_pub.publish(laserscan_msg)

        except Exception as e:
            self.get_logger().error(f'Ошибка получения скана: {e}')

    def status_timer_callback(self):
        """Таймер для публикации статуса."""
        if self.lidar:
            if self.lidar.is_connected:
                # Проверяем атрибут scanning если он есть
                if hasattr(self.lidar, 'scanning') and self.lidar.scanning:
                    status = 'scanning'
                else:
                    status = 'connected'
            else:
                status = 'disconnected'
        else:
            status = 'not_initialized'

        self.publish_status(status)

    def publish_status(self, status: str):
        """Публикует статус лидара."""
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)

    def destroy_node(self):
        """Очистка при завершении узла."""
        if self.lidar:
            self.lidar.disconnect()
        super().destroy_node()


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = LidarNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

