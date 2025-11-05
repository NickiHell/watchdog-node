# Конфигурация STM32 через STM32CubeMX

Подробная инструкция по настройке STM32F407 или STM32F411RE для WatchDog Robot через STM32CubeMX.

## Поддерживаемые платы

- **STM32F407VGTx** (рекомендуется, больше памяти)
- **STM32F411RE** (NUCLEO-F411RE, совместимо)

## Шаг 1: Создание проекта

1. Откройте STM32CubeMX
2. File → New Project
3. Выберите микроконтроллер:
   - **STM32F407VGTx** (или вашу модель F407)
   - **STM32F411RETx** (для NUCLEO-F411RE)
4. Нажмите "Start Project"

## Шаг 2: Настройка системы

### System Core → SYS

- **Debug:** Serial Wire (SWD) - для отладки

### System Core → RCC

- **High Speed Clock (HSE):** Crystal/Ceramic Resonator
- **Low Speed Clock (LSE):** Disable (если не используется)

### Clock Configuration

- **STM32F407:** Настройте тактовую частоту на **168 MHz** (максимум для F407)
- **STM32F411RE:** Настройте тактовую частоту на **100 MHz** (максимум для F411, но можно использовать и меньше)

## Шаг 3: Настройка GPIO

### Левый мотор (Motor Left)

- **PA0:** GPIO_Output - Motor Left IN1
- **PA1:** GPIO_Output - Motor Left IN2
- **PA2:** GPIO_Output - Motor Left EN (PWM через TIM2)

### Правый мотор (Motor Right)

- **PA3:** GPIO_Output - Motor Right IN1
- **PA4:** GPIO_Output - Motor Right IN2
- **PA5:** GPIO_Output - Motor Right EN (PWM через TIM3)

## Шаг 4: Настройка таймеров

### TIM2 - PWM для левого мотора

- **Mode:** PWM Generation CH1
- **Channel1:** PA2 (или выбранный пин)
- **Prescaler:** Настроить для частоты PWM ~20kHz
  - При 168MHz системной частоты: Prescaler = 8399, Period = 999
- **Auto-reload preload:** Enable

### TIM3 - PWM для правого мотора

- **Mode:** PWM Generation CH1
- **Channel1:** PA5 (или выбранный пин)
- **Prescaler:** То же что для TIM2

### TIM4 - Энкодер левого мотора

- **Mode:** Encoder Mode
- **Channel1:** PB6 (TIM4_CH1)
- **Channel2:** PB7 (TIM4_CH2)
- **Encoder Mode:** Encoder Mode TI1 and TI2
- **Polarity:** Rising Edge
- **Auto-reload preload:** Disable

### TIM5 - Энкодер правого мотора

- **Mode:** Encoder Mode
- **Channel1:** PA0 (TIM5_CH1) - **ВНИМАНИЕ:** Если PA0 используется для мотора, выберите другой пин
- **Channel2:** PA1 (TIM5_CH2) - **ВНИМАНИЕ:** Если PA1 используется для мотора, выберите другой пин
- **Encoder Mode:** Encoder Mode TI1 and TI2
- **Polarity:** Rising Edge

**ВАЖНО:** TIM5_CH1 и TIM5_CH2 могут конфликтовать с пинами моторов. Используйте альтернативные пины, например:
- **TIM5_CH1:** PA0 → PB0 или PC0
- **TIM5_CH2:** PA1 → PB1 или PC1

Или используйте TIM8 для второго энкодера.

## Шаг 5: Настройка UART

### USART1 - Коммуникация с ROS2

- **Mode:** Asynchronous
- **Baud Rate:** 115200
- **Word Length:** 8 Bits
- **Parity:** None
- **Stop Bits:** 1
- **RX:** PA10 (USART1_RX)
- **TX:** PA9 (USART1_TX)
- **NVIC Settings:** Enable USART1 global interrupt (опционально, для прерываний)

## Шаг 6: Генерация кода

1. Project Manager → Project Settings
   - **Toolchain/IDE:** STM32CubeIDE
   - **Project Name:** watchdog_robot
   - Выберите путь сохранения

2. Code Generator
   - Выберите структуру кода
   - Включите "Generate peripheral initialization as a pair of .c/.h files per peripheral"

3. Generate Code

## Шаг 7: Добавление пользовательского кода

После генерации кода добавьте файлы:
- `motor_control.c/h`
- `encoder_reader.c/h`
- `communication.c/h`

И интегрируйте их в `main.c` как показано в `main.c` примере.

## Альтернативная конфигурация пинов

Если пины конфликтуют, можно использовать:

### Вариант 1: Другие пины для энкодеров

**TIM4 (Левый энкодер):**
- CH1: PB6
- CH2: PB7

**TIM8 (Правый энкодер):**
- CH1: PC6 (TIM8_CH1)
- CH2: PC7 (TIM8_CH2)

### Вариант 2: Другие пины для моторов

Можно использовать другие GPIO для управления направлением:
- Левый мотор IN1/IN2: PB0, PB1
- Правый мотор IN1/IN2: PB10, PB11

## Тестирование

После прошивки:

1. Подключите STM32 к компьютеру через UART
2. Запустите ROS2 узел: `ros2 run watchdog_stm32_interface stm32_interface_node`
3. Отправьте команду: `ros2 topic pub /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.0}}"`
4. Проверьте ответ: `ros2 topic echo /odom`

## Примечания для STM32F411RE

**Важно:** STM32F411RE имеет меньше пинов, чем F407, но для данного проекта достаточно:

- **UART1 (PA9/PA10):** ✅ Доступен
- **TIM2 (PWM левого мотора):** ✅ Доступен
- **TIM3 (PWM правого мотора):** ✅ Доступен
- **TIM4 (Энкодер левого мотора):** ✅ Доступен (PB6/PB7)
- **TIM8 (Энкодер правого мотора):** ✅ Доступен (PC6/PC7)

**Отличия F411 от F407:**
- Меньше Flash памяти (512KB vs 1MB) - достаточно для проекта
- Меньше RAM (128KB vs 192KB) - достаточно для проекта
- Меньше пинов, но все необходимые доступны

**Рекомендация:** Используйте TIM8 для правого энкодера вместо TIM5, чтобы избежать конфликтов пинов.

## Общие примечания

- Все настройки зависят от вашей конкретной платы
- Проверьте распиновку вашей платы перед конфигурацией
- Некоторые пины могут быть заняты другими функциями
- Для F411RE используйте частоту 100MHz (максимум)

