import asyncio
import rclpy

from app.ros2_ws.src.core.core.dynamic import VelocityPublisher
from app.ros2_ws.src.core.core.scheduler import Scheduler


async def main(args=None):
    rclpy.init(args=args)
    topics = [
        (VelocityPublisher, None, None)
    ]
    scheduler = Scheduler()
    await scheduler.schedule(topics)

    # minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
