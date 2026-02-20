# Состояние контроллера WatchDog Drone
# Сообщение о текущем состоянии контроллера дрона

std_msgs/Header header

# Текущий режим работы
# Возможные значения: "idle", "takeoff", "navigating", "hovering", "landing", "tracking", "error"
string mode

# Активны ли подсистемы
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

# Время работы в секундах
float64 uptime

# Дополнительная информация
string status_message
