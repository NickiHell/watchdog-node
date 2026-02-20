"""Launch файл для запуска только mavros и Pixhawk интерфейса."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Генерация launch описания."""

    fcu_url = LaunchConfiguration("fcu_url")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "fcu_url", default_value="serial:///dev/ttyACM0:57600", description="URL подключения к Pixhawk"
            ),
            # Запуск mavros
            Node(
                package="mavros",
                executable="mavros_node",
                name="mavros",
                parameters=[
                    {"fcu_url": fcu_url},
                    {"system_id": 1},
                    {"component_id": 191},
                    {"target_system_id": 1},
                    {"target_component_id": 1},
                ],
                output="screen",
            ),
            # Интерфейс с Pixhawk
            Node(
                package="watchdog_pixhawk_interface",
                executable="pixhawk_interface_node",
                name="pixhawk_interface",
                output="screen",
            ),
        ]
    )
