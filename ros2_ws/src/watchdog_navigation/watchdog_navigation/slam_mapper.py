"""Модуль SLAM для построения карты на основе данных лидара.

Интегрируется с slam_toolbox для построения карты и локализации.
"""

import rclpy
from rclpy.node import Node
from rclpy.logging import get_logger
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid, MapMetaData
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_msgs.msg import String
import numpy as np
from typing import Optional


class SLAMMapper:
    """Класс для построения карты и локализации."""

    def __init__(self, node: Node):
        """Инициализирует SLAM модуль.

        Args:
            node: ROS2 узел для работы с топиками
        """
        self.node = node
        self.logger = get_logger('SLAMMapper')

        # Состояние
        self.map: Optional[OccupancyGrid] = None
        self.pose: Optional[PoseWithCovarianceStamped] = None
        self.map_received = False
        self.pose_received = False

        # Подписчики (SLAM данные публикуются slam_toolbox или другими узлами)
        self.map_sub = node.create_subscription(
            OccupancyGrid,
            '/map',
            self.map_callback,
            10
        )

        self.map_metadata_sub = node.create_subscription(
            MapMetaData,
            '/map_metadata',
            self.map_metadata_callback,
            10
        )

        self.pose_sub = node.create_subscription(
            PoseWithCovarianceStamped,
            '/pose',
            self.pose_callback,
            10
        )

        # Для slam_toolbox
        self.initial_pose_sub = node.create_subscription(
            PoseWithCovarianceStamped,
            '/initialpose',
            self.initial_pose_callback,
            10
        )

        self.logger.info('SLAM модуль инициализирован')

    def map_callback(self, msg: OccupancyGrid):
        """Обработчик обновления карты.

        Args:
            msg: Сообщение карты
        """
        self.map = msg
        self.map_received = True
        self.logger.debug(f'Карта обновлена: {msg.info.width}x{msg.info.height}, разрешение: {msg.info.resolution}')

    def map_metadata_callback(self, msg: MapMetaData):
        """Обработчик метаданных карты.

        Args:
            msg: Метаданные карты
        """
        self.logger.debug(f'Метаданные карты: разрешение={msg.resolution}, размер={msg.width}x{msg.height}')

    def pose_callback(self, msg: PoseWithCovarianceStamped):
        """Обработчик обновления позиции робота.

        Args:
            msg: Позиция робота
        """
        self.pose = msg
        self.pose_received = True
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        self.logger.debug(f'Позиция обновлена: x={x:.2f}, y={y:.2f}')

    def initial_pose_callback(self, msg: PoseWithCovarianceStamped):
        """Обработчик начальной позиции (для локализации).

        Args:
            msg: Начальная позиция
        """
        self.logger.info(f'Установлена начальная позиция: x={msg.pose.pose.position.x:.2f}, y={msg.pose.pose.position.y:.2f}')

    def is_ready(self) -> bool:
        """Проверяет, готова ли система SLAM.

        Returns:
            True если карта и позиция получены
        """
        return self.map_received and self.pose_received

    def get_map(self) -> Optional[OccupancyGrid]:
        """Получает текущую карту.

        Returns:
            Карта или None
        """
        return self.map

    def get_pose(self) -> Optional[PoseWithCovarianceStamped]:
        """Получает текущую позицию робота.

        Returns:
            Позиция или None
        """
        return self.pose

    def get_robot_position(self) -> Optional[tuple]:
        """Получает позицию робота в виде (x, y).

        Returns:
            Кортеж (x, y) или None
        """
        if self.pose:
            pos = self.pose.pose.pose.position
            return (pos.x, pos.y)
        return None

    def check_obstacle_in_map(self, x: float, y: float) -> bool:
        """Проверяет, есть ли препятствие в заданной точке карты.

        Args:
            x: Координата X (метры)
            y: Координата Y (метры)

        Returns:
            True если есть препятствие
        """
        if not self.map:
            return False

        # Конвертируем мировые координаты в координаты карты
        map_x = int((x - self.map.info.origin.position.x) / self.map.info.resolution)
        map_y = int((y - self.map.info.origin.position.y) / self.map.info.resolution)

        # Проверяем границы
        if map_x < 0 or map_x >= self.map.info.width or map_y < 0 or map_y >= self.map.info.height:
            return True  # Вне карты - считаем препятствием

        # Получаем значение ячейки
        index = map_y * self.map.info.width + map_x
        if index >= len(self.map.data):
            return True

        cell_value = self.map.data[index]

        # 0 = свободно, -1 = неизвестно, 100 = препятствие
        return cell_value > 50  # Порог для препятствия

    def get_map_data_as_array(self) -> Optional[np.ndarray]:
        """Получает данные карты как numpy array.

        Returns:
            2D массив значений карты или None
        """
        if not self.map:
            return None

        width = self.map.info.width
        height = self.map.info.height
        data = np.array(self.map.data, dtype=np.int8).reshape((height, width))

        return data

