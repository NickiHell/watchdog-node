"""
Root conftest.py — мокирует ROS2 и hardware-модули для запуска pytest в CI
без установленного ROS2 окружения.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Добавляем все ROS2-пакеты из src/ в sys.path, чтобы тесты могли их импортировать
_src = Path(__file__).parent / "ros2_ws" / "src"
for _pkg in sorted(_src.iterdir()):
    if _pkg.is_dir() and not _pkg.name.startswith("."):
        sys.path.insert(0, str(_pkg))


def _make_mock(name: str) -> MagicMock:
    mock = MagicMock()
    mock.__name__ = name
    return mock


ROS2_MODULES = [
    # rclpy core
    "rclpy",
    "rclpy.node",
    "rclpy.logging",
    "rclpy.timer",
    "rclpy.clock",
    "rclpy.duration",
    "rclpy.time",
    "rclpy.qos",
    "rclpy.callback_groups",
    "rclpy.executors",
    "rclpy.parameter",
    "rclpy.exceptions",
    # std_msgs
    "std_msgs",
    "std_msgs.msg",
    # sensor_msgs
    "sensor_msgs",
    "sensor_msgs.msg",
    # geometry_msgs
    "geometry_msgs",
    "geometry_msgs.msg",
    # nav_msgs
    "nav_msgs",
    "nav_msgs.msg",
    # mavros_msgs
    "mavros_msgs",
    "mavros_msgs.msg",
    "mavros_msgs.srv",
    # watchdog_msgs (custom)
    "watchdog_msgs",
    "watchdog_msgs.msg",
    # cv_bridge
    "cv_bridge",
    # hardware
    "pigpio",
    "w1thermsensor",
    "RPi",
    "RPi.GPIO",
]

for _mod in ROS2_MODULES:
    sys.modules.setdefault(_mod, _make_mock(_mod))
