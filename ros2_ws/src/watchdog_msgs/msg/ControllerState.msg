# Состояние контроллера WatchDog
# Сообщение о текущем состоянии контроллера робота

std_msgs/Header header

# Текущий режим работы
# Возможные значения: "idle", "navigation", "tracking", "error"
string mode

# Активны ли подсистемы
bool lidar_active
bool camera_active
bool face_detection_active
bool speech_active
bool navigation_active
bool stm32_connected

# Статус батареи (0-100)
uint8 battery_level

# Время работы в секундах
float64 uptime

# Дополнительная информация
string status_message

