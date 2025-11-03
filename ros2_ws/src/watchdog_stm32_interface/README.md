# watchdog_stm32_interface

ROS2 пакет для связи с STM32 микроконтроллером по протоколу из основного README.

## Функции

- Прием команд движения (`/cmd_vel`) и отправка их на STM32
- Чтение данных энкодеров от STM32
- Публикация odometry данных (`/odom`)
- Публикация статуса соединения (`/stm32/status`)

## Установка зависимостей

```bash
pip install pyserial
```

Или добавьте в `requirements.txt` вашего проекта:
```
pyserial>=3.5
```

## Использование

### Запуск узла

```bash
ros2 run watchdog_stm32_interface stm32_interface_node
```

### С параметрами

```bash
ros2 run watchdog_stm32_interface stm32_interface_node --ros-args \
  -p port:=/dev/ttyACM0 \
  -p baudrate:=115200 \
  -p timeout:=0.1 \
  -p cmd_vel_timeout:=0.5 \
  -p encoder_rate:=50.0 \
  -p wheel_radius:=0.05 \
  -p wheel_base:=0.25 \
  -p encoder_resolution:=360
```

### Отправка команды движения

```bash
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.0}}"
```

### Просмотр odometry

```bash
ros2 topic echo /odom
```

### Просмотр статуса

```bash
ros2 topic echo /stm32/status
```

## Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `port` | string | `/dev/ttyACM0` | Путь к последовательному порту |
| `baudrate` | int | `115200` | Скорость передачи |
| `timeout` | double | `0.1` | Таймаут чтения (секунды) |
| `cmd_vel_timeout` | double | `0.5` | Таймаут для остановки при отсутствии команд |
| `encoder_rate` | double | `50.0` | Частота чтения энкодеров (Гц) |
| `wheel_radius` | double | `0.05` | Радиус колеса (метры) |
| `wheel_base` | double | `0.25` | Расстояние между колесами (метры) |
| `encoder_resolution` | int | `360` | Тиков энкодера на оборот |

## Топики

### Подписки

- `/cmd_vel` (geometry_msgs/Twist) - Команды движения

### Публикации

- `/odom` (nav_msgs/Odometry) - Данные одометрии на основе энкодеров
- `/stm32/status` (std_msgs/String) - Статус соединения со STM32

## Протокол связи

Протокол полностью описан в основном README проекта. Основные характеристики:

- Заголовок: `[0xAA, 0x55]`
- Контрольная сумма: XOR всех байт
- Команда движения: заголовок + тип(0x01) + linear.x(4 байта float) + angular.z(4 байта float) + checksum
- Ответ энкодеров: заголовок + тип(0x12) + left(4 байта int32) + right(4 байта int32) + timestamp(4 байта uint32) + checksum

## Модули

### `protocol.py`

Класс `STM32Protocol` для кодирования/декодирования сообщений:
- `encode_movement_command()` - кодирует команду движения
- `encode_status_request()` - кодирует запрос состояния
- `decode_response()` - декодирует ответ от STM32

### `serial_interface.py`

Класс `SerialInterface` для работы с последовательным портом:
- `connect()` - открывает соединение
- `send_command()` - отправляет команду
- `read_response()` - читает ответ

### `stm32_interface_node.py`

Основной ROS2 узел, координирующий работу протокола и публикацию данных.

## Отладка

### Проверка порта

```bash
ls -l /dev/ttyACM*
```

### Просмотр данных порта (для отладки)

```bash
cat /dev/ttyACM0 | hexdump -C
```

### Тестирование протокола

Используйте `ros2 topic pub` для отправки команд и `ros2 topic echo` для просмотра ответов.

## Примечания

- Убедитесь, что пользователь добавлен в группу `dialout` для доступа к последовательному порту:
  ```bash
  sudo usermod -a -G dialout $USER
  ```
  После этого перелогиньтесь.

- При проблемах с доступом к порту проверьте права:
  ```bash
  sudo chmod 666 /dev/ttyACM0
  ```

- Для автозапуска узла используйте launch файлы (см. `config/launch/default.launch.py`)

