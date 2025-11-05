# watchdog_msgs

Пакет с кастомными ROS2 сообщениями для проекта WatchDog Robot.

## Сообщения

### ControllerState.msg
Состояние контроллера робота:
- Текущий режим работы
- Статус всех подсистем
- Уровень батареи
- Время работы

### FaceDetection.msg
Информация об одном обнаруженном лице:
- ID и имя человека
- Уверенность распознавания
- Координаты лица на изображении

### FaceDetections.msg
Список всех обнаруженных лиц на изображении:
- Массив объектов FaceDetection
- Общее количество лиц

### RobotStatus.msg
Общий статус робота:
- Статус системы (operational/warning/error/emergency_stop)
- Использование ресурсов (CPU, память)
- Температура
- Детальное состояние контроллера

## Использование

После сборки пакета можно использовать сообщения в других пакетах:

```python
from watchdog_msgs.msg import ControllerState, FaceDetections

# В setup.py добавьте зависимость:
# install_requires=['watchdog_msgs']
```

## Сборка

```bash
cd ros2_ws
colcon build --packages-select watchdog_msgs
source install/setup.bash
```

