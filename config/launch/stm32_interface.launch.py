from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            'port',
            default_value='/dev/ttyACM0',
            description='Serial port path for STM32 communication'
        ),
        DeclareLaunchArgument(
            'baudrate',
            default_value='115200',
            description='Serial port baudrate'
        ),
        DeclareLaunchArgument(
            'timeout',
            default_value='0.1',
            description='Serial port timeout in seconds'
        ),
        
        Node(
            package='watchdog_stm32_interface',
            executable='stm32_interface_node',
            name='stm32_interface_node',
            parameters=[{
                'port': LaunchConfiguration('port'),
                'baudrate': LaunchConfiguration('baudrate'),
                'timeout': LaunchConfiguration('timeout'),
                'cmd_vel_timeout': 0.5,
                'encoder_rate': 50.0,
                'wheel_radius': 0.05,
                'wheel_base': 0.25,
                'encoder_resolution': 360,
            }],
            output='screen',
            remappings=[
                ('/cmd_vel', '/cmd_vel'),
                ('/odom', '/odom'),
            ]
        ),
    ])

