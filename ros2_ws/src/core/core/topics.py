
from rclpy.node import Node

import random


from std_msgs.msg import String
class VelocityPublisher(Node):

    def __init__(self):
        super().__init__('velocity_publisher')
        self.publisher = self.create_publisher(String, 'sensors', 10)
        timer_period = 10.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)
        self.i = 0

    def timer_callback(self):
        msg = String()
        msg.data = str(random.randint(1, 255))
        self.publisher.publish(msg)
        self.get_logger().info('Publishing: "%s"' % msg.data)
        self.i += 1
