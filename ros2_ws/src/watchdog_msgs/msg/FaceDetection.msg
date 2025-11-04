# Информация об одном обнаруженном лице

# ID человека в базе данных
string person_id

# Имя человека
string name

# Уверенность распознавания (0.0 - 1.0)
float64 confidence

# Координаты ограничивающего прямоугольника
# x, y - верхний левый угол
# width, height - размеры
geometry_msgs/Point position
float64 width
float64 height

# Временная метка обнаружения
std_msgs/Header header

