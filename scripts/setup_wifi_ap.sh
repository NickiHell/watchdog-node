#!/bin/bash
# Скрипт настройки WiFi точки доступа для дрона

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Настройка WiFi точки доступа для WatchDog Drone ===${NC}"

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Ошибка: Запустите скрипт с правами root (sudo)${NC}"
    exit 1
fi

# Параметры WiFi точки доступа
SSID="WatchDog-Drone"
PASSWORD="watchdog123"
INTERFACE="wlan0"
CHANNEL="6"
COUNTRY_CODE="RU"

echo -e "${YELLOW}Параметры WiFi точки доступа:${NC}"
echo "  SSID: $SSID"
echo "  Пароль: $PASSWORD"
echo "  Интерфейс: $INTERFACE"
echo "  Канал: $CHANNEL"
echo "  Страна: $COUNTRY_CODE"
echo ""

# Проверка наличия интерфейса
if ! ip link show $INTERFACE &> /dev/null; then
    echo -e "${RED}Ошибка: Интерфейс $INTERFACE не найден${NC}"
    exit 1
fi

# Установка необходимых пакетов
echo -e "${YELLOW}Установка необходимых пакетов...${NC}"
apt-get update
apt-get install -y hostapd dnsmasq iptables-persistent netfilter-persistent

# Остановка сервисов
echo -e "${YELLOW}Остановка сервисов...${NC}"
systemctl stop hostapd
systemctl stop dnsmasq

# Настройка hostapd
echo -e "${YELLOW}Настройка hostapd...${NC}"
cat > /etc/hostapd/hostapd.conf << EOF
interface=$INTERFACE
driver=nl80211
ssid=$SSID
hw_mode=g
channel=$CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code=$COUNTRY_CODE
EOF

# Настройка dnsmasq
echo -e "${YELLOW}Настройка dnsmasq...${NC}"
# Резервная копия оригинального файла
if [ -f /etc/dnsmasq.conf ]; then
    cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
fi

cat > /etc/dnsmasq.conf << EOF
interface=$INTERFACE
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
domain=watchdog.local
address=/#/192.168.4.1
EOF

# Настройка статического IP для интерфейса
echo -e "${YELLOW}Настройка статического IP...${NC}"
cat > /etc/netplan/99-wifi-ap.yaml << EOF
network:
  version: 2
  renderer: networkd
  wifis:
    $INTERFACE:
      addresses:
        - 192.168.4.1/24
      nameservers:
        addresses: [8.8.8.8, 8.8.4.4]
EOF

# Настройка IP forwarding и NAT
echo -e "${YELLOW}Настройка IP forwarding и NAT...${NC}"
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# Определение основного интерфейса (обычно eth0)
MAIN_INTERFACE=$(ip route | grep default | awk '{print $5}' | head -1)
if [ -z "$MAIN_INTERFACE" ]; then
    MAIN_INTERFACE="eth0"
fi

echo -e "${YELLOW}Основной интерфейс: $MAIN_INTERFACE${NC}"

# Настройка iptables для NAT
iptables -t nat -A POSTROUTING -o $MAIN_INTERFACE -j MASQUERADE
iptables -A FORWARD -i $MAIN_INTERFACE -o $INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $INTERFACE -o $MAIN_INTERFACE -j ACCEPT

# Сохранение правил iptables
netfilter-persistent save

# Включение автозапуска сервисов
echo -e "${YELLOW}Включение автозапуска сервисов...${NC}"
systemctl enable hostapd
systemctl enable dnsmasq

# Применение настроек netplan
netplan apply

# Запуск сервисов
echo -e "${YELLOW}Запуск сервисов...${NC}"
systemctl start hostapd
systemctl start dnsmasq

echo ""
echo -e "${GREEN}=== WiFi точка доступа настроена! ===${NC}"
echo -e "${GREEN}SSID: $SSID${NC}"
echo -e "${GREEN}Пароль: $PASSWORD${NC}"
echo -e "${GREEN}IP адрес точки доступа: 192.168.4.1${NC}"
echo ""
echo -e "${YELLOW}Для подключения:${NC}"
echo "  1. Найдите WiFi сеть '$SSID'"
echo "  2. Введите пароль: $PASSWORD"
echo "  3. Откройте браузер и перейдите на http://192.168.4.1:8000"
echo ""
