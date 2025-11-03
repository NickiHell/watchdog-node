from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    config_path = PathJoinSubstitution([
        FindPackageShare('watchdog_controller'),
        'config',
        'robot_config.yaml'
    ])

    return LaunchDescription([
        DeclareLaunchArgument(
            'config_file',
            default_value=config_path,
            description='Path to robot configuration file'
        ),
        
        # Лидар узел
        Node(
            package='watchdog_lidar',
            executable='lidar_node',
            name='lidar_node',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),
        
        # Камера узел
        Node(
            package='watchdog_camera',
            executable='camera_node',
            name='camera_node',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),
        
        # Распознавание лиц
        Node(
            package='watchdog_face_detection',
            executable='face_detection_node',
            name='face_detection_node',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),
        
        # Обработка речи
        Node(
            package='watchdog_speech',
            executable='speech_node',
            name='speech_node',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),
        
        # Навигация
        Node(
            package='watchdog_navigation',
            executable='navigation_node',
            name='navigation_node',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),
        
        # Главный контроллер
        Node(
            package='watchdog_controller',
            executable='controller_node',
            name='controller_node',
            parameters=[LaunchConfiguration('config_file')],
            output='screen'
        ),
    ])

