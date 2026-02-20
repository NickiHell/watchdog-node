#!/bin/bash
# Скрипт установки зависимостей проекта

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Установка зависимостей WatchDog Drone ===${NC}"

# Проверка прав root для системных пакетов
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Предупреждение: Некоторые пакеты требуют прав root${NC}"
    SUDO=""
else
    SUDO=""
fi

# Обновление списка пакетов
echo -e "${YELLOW}Обновление списка пакетов...${NC}"
$SUDO apt-get update

# Установка системных зависимостей
echo -e "${YELLOW}Установка системных зависимостей...${NC}"
$SUDO apt-get install -y \
    python3-pip \
    python3-dev \
    python3-setuptools \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    vim \
    net-tools \
    iptables \
    hostapd \
    dnsmasq \
    iptables-persistent \
    netfilter-persistent

# Установка ROS2 зависимостей (если ROS2 установлен)
if command -v ros2 &> /dev/null; then
    echo -e "${YELLOW}Установка ROS2 зависимостей...${NC}"
    $SUDO apt-get install -y \
        ros-humble-mavros \
        ros-humble-mavros-extras \
        ros-humble-cv-bridge \
        ros-humble-image-transport \
        ros-humble-image-geometry \
        python3-colcon-common-extensions
else
    echo -e "${YELLOW}ROS2 не найден. Пропускаем установку ROS2 зависимостей.${NC}"
fi

# Установка Python зависимостей (uv или pip)
echo -e "${YELLOW}Установка Python зависимостей...${NC}"
cd "$(dirname "$0")/.."
if command -v uv >/dev/null 2>&1; then
    uv sync --group ml --group hardware
else
    pip3 install --user -r requirements.txt 2>/dev/null || pip3 install --user numpy opencv-python pymavlink pyserial pyyaml psutil
fi

echo ""
echo -e "${GREEN}=== Зависимости установлены! ===${NC}"
echo ""
echo -e "${YELLOW}Следующие шаги:${NC}"
echo "  1. Настройте ROS2 workspace: cd ros2_ws && colcon build"
echo "  2. Настройте WiFi точку доступа: sudo bash scripts/setup_wifi_ap.sh"
echo "  3. Настройте Pixhawk согласно документации"
echo ""
