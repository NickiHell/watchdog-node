# Multi-stage build для WatchDog Drone
FROM osrf/ros:humble-desktop-full AS base

# Устанавливаем uv для управления зависимостями
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-vcstool \
    build-essential \
    git \
    ros-humble-mavros \
    ros-humble-mavros-extras \
    ros-humble-cv-bridge \
    python3-pigpio \
    pigpiod \
    python3-rpi.gpio \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей через uv
WORKDIR /workspace
COPY pyproject.toml uv.lock ./
# Экспортируем из lockfile и устанавливаем системный Python (совместимо с ROS2)
RUN uv export --frozen --no-dev --group ml --group hardware \
    | pip3 install --no-cache-dir -r /dev/stdin

# Копирование конфигурации и рабочего пространства ROS2
COPY config/ /workspace/config/
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

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Установка runtime системных зависимостей
RUN apt-get update && apt-get install -y \
    python3-pip \
    ros-humble-mavros \
    ros-humble-mavros-extras \
    ros-humble-cv-bridge \
    python3-pigpio \
    pigpiod \
    python3-rpi.gpio \
    && rm -rf /var/lib/apt/lists/*

# Копирование установленных пакетов из base
COPY --from=base /workspace/ros2_ws/install /workspace/ros2_ws/install
COPY --from=base /workspace/pyproject.toml /workspace/pyproject.toml
COPY --from=base /workspace/uv.lock /workspace/uv.lock

# Установка runtime Python зависимостей
RUN uv export --frozen --no-dev --group ml --group hardware \
    | pip3 install --no-cache-dir -r /dev/stdin

WORKDIR /workspace

# Настройка окружения
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /workspace/ros2_ws/install/setup.bash" >> ~/.bashrc

CMD ["bash", "-c", "source /opt/ros/humble/setup.bash && \
     source /workspace/ros2_ws/install/setup.bash && \
     ros2 launch config/launch/drone_full.launch.py"]
