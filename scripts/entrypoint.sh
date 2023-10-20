#!/bin/bash
set -e

source /opt/ros/iron/setup.bash
source /app/ros2_ws/install/setup.bash
cd /app/ros2_ws/
rosdep install -i --from-path src --rosdistro iron -y
colcon build

exec "$@"
