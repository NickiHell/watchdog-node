# Статус дрона WatchDog
# Общее сообщение о статусе дрона

std_msgs/Header header

# Текущий режим работы
string mode

# Статус подсистем
bool lidar_active
bool camera_active
bool face_detection_active
bool navigation_active
bool pixhawk_connected
bool rc_active

# Статус батареи (0-100)
uint8 battery_level

# Высота полета (м)
float32 altitude

# Скорость (м/с)
float32 speed

# Время работы в секундах
float64 uptime

# Дополнительная информация
string status_message
