"""Unit тесты для базового класса лидара."""

import pytest
from watchdog_lidar.lidar_base import LidarScan


class TestLidarScan:
    """Тесты для LidarScan."""

    def test_lidar_scan_init(self):
        """Тест инициализации LidarScan."""
        scan = LidarScan()
        assert scan.ranges == []
        assert scan.angles == []
        assert scan.intensities == []
        assert scan.timestamp == 0.0

    def test_lidar_scan_to_laserscan_empty(self):
        """Тест конвертации пустого скана в LaserScan."""
        scan = LidarScan()
        msg = scan.to_laserscan('test_frame')

        assert msg.header.frame_id == 'test_frame'
        assert msg.angle_min == -3.14159  # Значение по умолчанию
        assert msg.angle_max == 3.14159
        assert msg.range_min == 0.05
        assert msg.range_max == 12.0
        assert msg.ranges == []
        assert msg.intensities == []

    def test_lidar_scan_to_laserscan_with_data(self):
        """Тест конвертации скана с данными в LaserScan."""
        scan = LidarScan()
        scan.ranges = [0.5, 1.0, 1.5, 2.0]
        scan.angles = [0.0, 0.5, 1.0, 1.5]
        scan.intensities = [100, 200, 300, 400]
        scan.timestamp = 123.45

        msg = scan.to_laserscan('lidar_frame')

        assert msg.header.frame_id == 'lidar_frame'
        assert msg.angle_min == 0.0
        assert msg.angle_max == 1.5
        assert msg.range_min == 0.5
        assert msg.range_max == 2.0
        assert len(msg.ranges) == 4
        assert len(msg.intensities) == 4
        assert msg.ranges == [0.5, 1.0, 1.5, 2.0]
        assert msg.intensities == [100, 200, 300, 400]

    def test_lidar_scan_to_laserscan_single_point(self):
        """Тест конвертации скана с одной точкой."""
        scan = LidarScan()
        scan.ranges = [1.0]
        scan.angles = [0.0]

        msg = scan.to_laserscan()

        assert msg.angle_increment == pytest.approx(0.0174533, rel=1e-5)  # ~1 градус
        assert len(msg.ranges) == 1

