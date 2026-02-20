# Один обнаруженный/отслеживаемый объект (YOLOv8n + ByteTrack)

std_msgs/Header header

int32 track_id       # уникальный ID трека ByteTrack (-1 если нет трека)
int32 class_id       # ID класса YOLO
string class_name    # имя класса (person, car, ...)
float32 confidence   # вероятность детекции [0.0, 1.0]

# Bounding box в пикселях изображения
float32 bbox_x       # левый край
float32 bbox_y       # верхний край
float32 bbox_w       # ширина
float32 bbox_h       # высота

# Центр объекта, нормализованный [-0.5, 0.5] (0,0 = центр кадра)
float32 center_x
float32 center_y
