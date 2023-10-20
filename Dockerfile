FROM ros:iron

WORKDIR /app


RUN apt-get update && apt-get install -y \
      python3-pip python3-setuptools \
      python3-virtualenv python3-wheel \
      ros-${ROS_DISTRO}-demo-nodes-py && \
    rm -rf /var/lib/apt/lists/*


COPY pyproject.toml requirements.txt ros2_ws scripts /app/
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["scripts/entrypoint.sh"]
CMD ["bash"]
