FROM ros:iron

WORKDIR /app

RUN apt-get update && apt-get install -y \
      ros-${ROS_DISTRO}-demo-nodes-cpp \
      python3-pip python3-setuptools \
      python3-virtualenv python3-wheel \
      ros-${ROS_DISTRO}-demo-nodes-py && \
    rm -rf /var/lib/apt/lists/*


COPY pyproject.toml /app/pyproject.toml
COPY requirements.txt /app/requirements.txt
COPY ros2_ws/ /app/ros2_ws
COPY scripts/entrypoint.sh /app

RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["entrypoint.sh"]
CMD ["bash"]
