import random

import rclpy
from rclpy.node import Node

from std_msgs.msg import String


class VelocityPublisher(Node):
    def __init__(self):
        super().__init__('velocity_publisher')
        self.publisher = self.create_publisher(String, 'velocity', 10)
        self.timer = self.create_timer(10, self.timer_callback)

    def timer_callback(self):
        msg = String()
        msg.data = random.randint(1, 255)
        self.publisher.publish(msg)
        self.get_logger().info(msg.data)


def main(args=None):
    rclpy.init(args=args)

    velocity_pub = VelocityPublisher()

    rclpy.spin(velocity_pub)

    velocity_pub.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
