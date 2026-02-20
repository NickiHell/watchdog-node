"""Launch файл для полного запуска системы дрона Watchdog."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os


def generate_launch_description():
    """Генерация launch описания."""

    launch_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(launch_dir, "..", "drone_config.yaml")
    pixhawk_config_path = os.path.join(launch_dir, "..", "pixhawk_config.yaml")

    config_file = LaunchConfiguration("config_file")
    use_sim_time = LaunchConfiguration("use_sim_time")
    enable_rc = LaunchConfiguration("enable_rc")
    enable_detection = LaunchConfiguration("enable_detection")
    enable_gimbal = LaunchConfiguration("enable_gimbal")
    enable_thermal = LaunchConfiguration("enable_thermal")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "config_file", default_value=config_path, description="Путь к конфигурационному файлу"
            ),
            DeclareLaunchArgument("use_sim_time", default_value="false", description="Использовать симуляцию времени"),
            DeclareLaunchArgument("enable_rc", default_value="true", description="Включить RC интерфейс (TX16 ELRS)"),
            DeclareLaunchArgument(
                "enable_detection", default_value="true", description="Включить YOLOv8n + ByteTrack детекцию"
            ),
            DeclareLaunchArgument(
                "enable_gimbal", default_value="true", description="Включить управление подвесом SIYI A8 mini"
            ),
            DeclareLaunchArgument(
                "enable_thermal", default_value="true", description="Включить термоуправление (вентилятор/нагреватель)"
            ),
            # MAVROS — мост между ROS2 и Pixhawk 4
            Node(
                package="mavros",
                executable="mavros_node",
                name="mavros",
                parameters=[
                    pixhawk_config_path,
                    {"fcu_url": "serial:///dev/ttyACM0:115200"},
                    {"system_id": 255},
                    {"component_id": 240},
                    {"target_system_id": 1},
                    {"target_component_id": 1},
                    {"use_sim_time": use_sim_time},
                ],
                output="screen",
            ),
            # Интерфейс с Pixhawk (телеметрия, команды)
            Node(
                package="watchdog_pixhawk_interface",
                executable="pixhawk_interface_node",
                name="pixhawk_interface",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                output="screen",
            ),
            # RC интерфейс TX16 ELRS (SBUS → Pixhawk → MAVROS → ROS2)
            Node(
                package="watchdog_pixhawk_interface",
                executable="rc_interface_node",
                name="rc_interface",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                condition=IfCondition(enable_rc),
                output="screen",
            ),
            # Навигационный стек (PX4 + RPLidar S2)
            Node(
                package="watchdog_navigation",
                executable="navigation_node",
                name="navigation",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                output="screen",
            ),
            # Драйвер RPLidar S2 (baudrate 1 000 000)
            Node(
                package="watchdog_lidar",
                executable="lidar_node",
                name="lidar",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                output="screen",
            ),
            # Камера SIYI A8 mini
            Node(
                package="watchdog_camera",
                executable="camera_node",
                name="camera",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                output="screen",
            ),
            # Детекция объектов YOLOv8n + ByteTrack (публикует /detection/tracks)
            Node(
                package="watchdog_detection",
                executable="detection_node",
                name="detection",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                condition=IfCondition(enable_detection),
                output="screen",
            ),
            # Управление подвесом SIYI A8 mini (MAVLink Gimbal v2 + автослежение)
            Node(
                package="watchdog_gimbal",
                executable="gimbal_node",
                name="gimbal",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                condition=IfCondition(enable_gimbal),
                output="screen",
            ),
            # Термоуправление (DS18B20 → вентилятор + нагреватель мачты)
            Node(
                package="watchdog_thermal",
                executable="thermal_node",
                name="thermal",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                condition=IfCondition(enable_thermal),
                output="screen",
            ),
            # Главный контроллер (state machine)
            Node(
                package="watchdog_controller",
                executable="controller_node",
                name="controller",
                parameters=[config_file, {"use_sim_time": use_sim_time}],
                output="screen",
            ),
        ]
    )
