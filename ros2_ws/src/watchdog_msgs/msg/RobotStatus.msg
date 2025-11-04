# Общий статус робота WatchDog

std_msgs/Header header

# Статус системы
# "operational" - работает нормально
# "warning" - есть предупреждения
# "error" - есть ошибки
# "emergency_stop" - аварийная остановка
string system_status

# Температура CPU (градусы Цельсия)
float32 cpu_temperature

# Использование памяти (0-100%)
uint8 memory_usage

# Использование CPU (0-100%)
uint8 cpu_usage

# Статус всех подсистем
watchdog_msgs/ControllerState controller_state

# Сообщение об ошибках (если есть)
string error_message

