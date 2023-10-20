#!/bin/bash
set -e

source /opt/ros/iron/setup.bash
source /app/ros2_ws/install/setup.bash
cd /app/ros2_ws/
colcon build

exec "$@"
