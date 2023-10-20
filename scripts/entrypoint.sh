#!/bin/bash

source /opt/ros/iron/setup.bash
cd /app/ros2_ws/src
colcon build
cd /app/ros2_ws
source install/setup.bash
colcon build


exec "$@"
