FROM ros:iron

WORKDIR /app


RUN apt-get update && apt-get install -y \
      python3-pip python3-setuptools \
      python3-virtualenv python3-wheel \
      ros-${ROS_DISTRO}-demo-nodes-py && \
    rm -rf /var/lib/apt/lists/*


COPY pyproject.toml requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY ./scripts/entrypoint.sh /app/
COPY ./ros2_ws /app/ros2_ws

ENTRYPOINT ["./entrypoint.sh"]
CMD ["bash"]
