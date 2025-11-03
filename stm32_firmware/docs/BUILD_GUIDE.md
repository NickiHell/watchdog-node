# Руководство по сборке и прошивке STM32

Подробная инструкция по сборке и загрузке прошивки на STM32.

## Метод 1: STM32CubeIDE (рекомендуется)

### Шаг 1: Установка STM32CubeIDE

1. Скачайте с [официального сайта ST](https://www.st.com/en/development-tools/stm32cubeide.html)
2. Установите следуя инструкциям
3. Запустите STM32CubeIDE

### Шаг 2: Создание проекта

1. **File → New → STM32 Project**
2. Выберите **STM32F407VGTx** (или вашу модель)
3. Назовите проект: `watchdog_robot`
4. Нажмите **Finish**

### Шаг 3: Настройка через CubeMX

1. В открывшемся окне CubeMX настройте:
   - UART1 (см. `STM32CubeMX_Configuration.md`)
   - Таймеры TIM2, TIM3, TIM4, TIM5
   - GPIO пины

2. **Project Manager → Code Generator**
   - Выберите структуру кода
   - Включите генерацию отдельных файлов

3. **Generate Code** (Ctrl+G)

### Шаг 4: Добавление пользовательского кода

После генерации кода:

1. **Скопируйте файлы** из `stm32_firmware/src/` в проект:
   ```
   watchdog_robot/
   ├── Core/
   │   ├── Src/
   │   │   ├── main.c (замените содержимое)
   │   │   ├── motor_control.c (добавьте)
   │   │   ├── encoder_reader.c (добавьте)
   │   │   └── communication.c (добавьте)
   │   └── Inc/
   │       ├── motor_control.h (добавьте)
   │       ├── encoder_reader.h (добавьте)
   │       └── communication.h (добавьте)
   ```

2. **Обновите main.c**:
   - Добавьте `#include "motor_control.h"` и другие
   - Добавьте вызовы инициализации
   - Добавьте основной цикл

3. **Проверьте компиляцию**: Build → Build Project (Ctrl+B)

### Шаг 5: Прошивка

1. Подключите ST-Link к STM32
2. Подключите ST-Link к компьютеру
3. **Run → Debug** (или F11)
4. Прошивка загрузится автоматически

## Метод 2: Команды (альтернатива)

### Компиляция через командную строку

Если у вас настроен ARM GCC toolchain:

```bash
# Используйте пример Makefile как основу
make -f Makefile.example
```

### Прошивка через OpenOCD

```bash
# Запустите OpenOCD
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# В другом терминале
telnet localhost 4444
> reset halt
> flash write_image erase watchdog_robot.hex
> reset
```

### Прошивка через st-flash

```bash
# Установите st-flash
sudo apt install stlink-tools

# Загрузите прошивку
st-flash write watchdog_robot.bin 0x8000000
```

## Проверка работы

### После прошивки

1. Подключите STM32 к Raspberry Pi через UART
2. Запустите ROS2 узел:
   ```bash
   ros2 run watchdog_stm32_interface stm32_interface_node
   ```

3. Проверьте подключение:
   ```bash
   ros2 topic echo /stm32/status
   ```

4. Отправьте тестовую команду:
   ```bash
   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
     "{linear: {x: 0.3}, angular: {z: 0.0}}"
   ```

5. Проверьте odometry:
   ```bash
   ros2 topic echo /odom
   ```

## Решение проблем

### Ошибка компиляции

1. Проверьте пути к HAL библиотекам
2. Убедитесь, что все заголовочные файлы включены
3. Проверьте настройки компилятора

### Ошибка прошивки

1. Проверьте подключение ST-Link
2. Проверьте питание STM32 (3.3V)
3. Попробуйте сброс: подключите BOOT0 к VCC, нажмите RESET, отключите BOOT0

### Проблемы с UART

1. Проверьте уровень сигналов (3.3V для STM32)
2. Проверьте скорость передачи (115200)
3. Проверьте подключение TX/RX (перекрестно)

## Отладка

### Использование отладчика

1. Установите breakpoints в коде
2. Запустите в режиме Debug
3. Используйте Variables view для просмотра значений

### Логирование через UART

Добавьте printf через UART:
```c
// В main.c после инициализации UART
printf("STM32 WatchDog Robot initialized\r\n");
```

Затем используйте serial monitor для просмотра логов.

## Оптимизация

### Для производительности

- Используйте оптимизацию компилятора: `-O2`
- Включите hardware floating point: `-mfloat-abi=hard`
- Оптимизируйте использование памяти

### Для размера

- Используйте `-Os` (optimize for size)
- Отключите отладочную информацию в release
- Используйте linker script для оптимизации секций

