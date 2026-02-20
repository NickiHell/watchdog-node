# Массив обнаруженных объектов за один кадр

std_msgs/Header header

watchdog_msgs/Detection[] detections

int32 frame_number   # номер обработанного кадра
bool yolo_frame      # true если на этом кадре запускался YOLO (не интерполяция ByteTrack)
