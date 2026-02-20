#!/usr/bin/env bash
# setup_mavproxy.sh — Установка и настройка MAVProxy на Raspberry Pi 5
# Назначение: форвардинг MAVLink Pixhawk 4 → Mission Planner / QGC через UDP
#
# Использование:
#   chmod +x scripts/setup_mavproxy.sh
#   sudo ./scripts/setup_mavproxy.sh

set -e

MAVPROXY_PORT=14550
MAVPROXY_PORT_QGC=14551
PIXHAWK_SERIAL="/dev/ttyACM0"
PIXHAWK_BAUD=115200
MAVPROXY_SERVICE="mavproxy"

echo "=== Watchdog: Установка MAVProxy ==="

# ── 1. Зависимости ─────────────────────────────────────────────────────────
echo "[1/4] Установка зависимостей..."
apt-get update -qq
apt-get install -y python3-pip python3-dev libxml2-dev libxslt1-dev

pip3 install --upgrade MAVProxy

# ── 2. Проверка установки ──────────────────────────────────────────────────
echo "[2/4] Проверка MAVProxy..."
mavproxy.py --version

# ── 3. Systemd сервис ──────────────────────────────────────────────────────
echo "[3/4] Создание systemd сервиса..."

MAVPROXY_BIN=$(which mavproxy.py || which mavproxy)

cat > /etc/systemd/system/${MAVPROXY_SERVICE}.service <<EOF
[Unit]
Description=MAVProxy — MAVLink форвардинг Pixhawk → Mission Planner
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=${MAVPROXY_BIN} \\
    --master=${PIXHAWK_SERIAL},${PIXHAWK_BAUD} \\
    --out=udpbcast:255.255.255.255:${MAVPROXY_PORT} \\
    --out=udpbcast:255.255.255.255:${MAVPROXY_PORT_QGC} \\
    --aircraft watchdog \\
    --daemon
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# ── 4. Включение сервиса ───────────────────────────────────────────────────
echo "[4/4] Включение и запуск сервиса..."
systemctl daemon-reload
systemctl enable ${MAVPROXY_SERVICE}
systemctl start ${MAVPROXY_SERVICE}

echo ""
echo "=== MAVProxy установлен и запущен ==="
echo ""
echo "Статус:     systemctl status ${MAVPROXY_SERVICE}"
echo "Логи:       journalctl -u ${MAVPROXY_SERVICE} -f"
echo "Остановить: systemctl stop ${MAVPROXY_SERVICE}"
echo ""
echo "Mission Planner: UDP ${MAVPROXY_PORT} (широковещательный)"
echo "QGroundControl:  UDP ${MAVPROXY_PORT_QGC}"
echo ""
echo "Настройки в: config/mavproxy_config.yaml"
