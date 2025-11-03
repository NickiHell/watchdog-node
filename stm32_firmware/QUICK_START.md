# Быстрый старт - STM32 прошивка

Краткое руководство по сборке и прошивке STM32 для WatchDog Robot.

## Шаг 1: Подготовка

1. Установите **STM32CubeIDE** с официального сайта ST
2. Откройте STM32CubeIDE

## Шаг 2: Создание проекта

1. **File → New → STM32 Project**
2. Выберите **STM32F407VGTx**
3. Назовите: `watchdog_robot`
4. **Finish**

## Шаг 3: Настройка в CubeMX

### UART1 (связь с ROS2)
- **Mode:** Asynchronous
- **Baud Rate:** 115200
- **RX:** PA10
- **TX:** PA9

### TIM2 (PWM левый мотор)
- **Mode:** PWM Generation CH1
- **Channel 1:** PA2
- **Prescaler:** 8399, **Period:** 999 (для ~20kHz)

### TIM3 (PWM правый мотор)
- **Mode:** PWM Generation CH1
- **Channel 1:** PA5
- **Prescaler:** 8399, **Period:** 999

### TIM4 (Энкодер левый)
- **Mode:** Encoder Mode
- **Channel 1:** PB6
- **Channel 2:** PB7

### TIM5 или TIM8 (Энкодер правый)
- **Mode:** Encoder Mode
- Если TIM5: используйте свободные пины (не PA0-PA1)
- Или TIM8: PC6, PC7

### GPIO
- **PA0, PA1:** Левый мотор IN1, IN2
- **PA3, PA4:** Правый мотор IN1, IN2

## Шаг 4: Генерация кода

1. **Project Manager:** Выберите путь и название проекта
2. **Code Generator:** Включите генерацию отдельных файлов
3. **Generate Code** (Ctrl+G)

## Шаг 5: Добавление кода

Скопируйте файлы из `stm32_firmware/src/` в проект:
- `motor_control.c/h`
- `encoder_reader.c/h`
- `communication.c/h`

Обновите `main.c`:
- Добавьте `#include` для всех модулей
- Добавьте вызовы инициализации после `MX_*_Init()`
- Добавьте основной цикл из примера

## Шаг 6: Компиляция и прошивка

1. **Build Project** (Ctrl+B)
2. Подключите ST-Link
3. **Run → Debug** (F11)
4. Прошивка загрузится автоматически

## Шаг 7: Проверка

1. Подключите STM32 к Raspberry Pi через UART
2. Запустите ROS2 узел:
   ```bash
   ros2 run watchdog_stm32_interface stm32_interface_node
   ```

3. Отправьте команду:
   ```bash
   ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
     "{linear: {x: 0.3}, angular: {z: 0.0}}"
   ```

4. Моторы должны вращаться!

## Проблемы?

См. подробное руководство в `docs/BUILD_GUIDE.md` и `STM32CubeMX_Configuration.md`.

