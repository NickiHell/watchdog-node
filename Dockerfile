# Multi-stage build для WatchDog Robot
FROM osrf/ros:humble-desktop-full AS base

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
WORKDIR /workspace
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Копирование рабочего пространства ROS2
COPY ros2_ws /workspace/ros2_ws

# Инициализация rosdep
RUN rosdep update

# Сборка ROS2 пакетов
WORKDIR /workspace/ros2_ws
RUN . /opt/ros/humble/setup.sh && \
    rosdep install --from-paths src --ignore-src -r -y || true && \
    colcon build --symlink-install

# Production stage
FROM osrf/ros:humble-desktop-full AS production

# Копирование установленных пакетов
COPY --from=base /workspace/ros2_ws/install /workspace/ros2_ws/install
COPY --from=base /workspace/requirements.txt /workspace/

# Установка только runtime зависимостей
RUN pip3 install --no-cache-dir -r /workspace/requirements.txt && \
    rm /workspace/requirements.txt

WORKDIR /workspace

# Настройка окружения
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /workspace/ros2_ws/install/setup.bash" >> ~/.bashrc

# По умолчанию запускаем основной launch файл
CMD ["bash", "-c", "source /opt/ros/humble/setup.bash && \
     source /workspace/ros2_ws/install/setup.bash && \
     ros2 launch watchdog_controller default.launch.py"]

