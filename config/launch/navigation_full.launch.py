from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os


def generate_launch_description():
    """Launch файл для полного запуска навигации со SLAM."""

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_slam',
            default_value='true',
            description='Использовать SLAM для построения карты'
        ),
        DeclareLaunchArgument(
            'map_file',
            default_value='',
            description='Путь к файлу карты для локализации (пусто = построение новой)'
        ),
        
        # Лидар
        Node(
            package='watchdog_lidar',
            executable='lidar_node',
            name='lidar_node',
            parameters=[{
                'lidar.type': 'rplidar',
                'lidar.port': '/dev/ttyUSB0',
                'lidar.baudrate': 115200,
            }],
            output='screen'
        ),
        
        # Одометрия (STM32)
        Node(
            package='watchdog_stm32_interface',
            executable='stm32_interface_node',
            name='stm32_interface_node',
            parameters=[{
                'port': '/dev/ttyACM0',
                'baudrate': 115200,
            }],
            output='screen'
        ),
        
        # SLAM (условно, только если use_slam=true)
        Node(
            package='slam_toolbox',
            executable='async_slam_toolbox_node',
            name='slam_toolbox_node',
            condition=IfCondition(LaunchConfiguration('use_slam')),
            parameters=[{
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',
                'scan_topic': '/sensor/lidar/scan',
            }],
            output='screen'
        ),
        
        # Навигация
        Node(
            package='watchdog_navigation',
            executable='navigation_node',
            name='navigation_node',
            parameters=[{
                'use_slam': LaunchConfiguration('use_slam'),
                'safety_distance': 0.3,
                'max_linear_velocity': 0.5,
                'max_angular_velocity': 1.0,
                'goal_tolerance': 0.1,
            }],
            output='screen'
        ),
    ])

