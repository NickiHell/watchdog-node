/**
 * @file main_example.c
 * @brief Пример использования протокола связи в main.c
 * 
 * Это примерная реализация. В реальном проекте нужно:
 * 1. Настроить UART через STM32CubeMX
 * 2. Настроить таймеры для энкодеров
 * 3. Настроить PWM для моторов
 * 4. Добавить обработку прерываний
 */

#include "main.h"
#include "communication.h"
#include "motor_control.h"  // Предполагаемый модуль управления моторами
#include "encoder_reader.h" // Предполагаемый модуль чтения энкодеров

extern UART_HandleTypeDef huart1;
extern TIM_HandleTypeDef htim2;  // PWM таймер для моторов
extern TIM_HandleTypeDef htim3;  // Таймер для энкодера левого мотора
extern TIM_HandleTypeDef htim4;  // Таймер для энкодера правого мотора

/**
 * @brief Основной цикл программы
 */
int main(void) {
    // Инициализация HAL
    HAL_Init();
    
    // Конфигурация системы (частота, UART, таймеры и т.д.)
    SystemClock_Config();
    MX_USART1_UART_Init();
    MX_TIM2_Init();
    MX_TIM3_Init();
    MX_TIM4_Init();
    
    // Инициализация модулей
    Communication_Init();
    MotorControl_Init();
    EncoderReader_Init();
    
    // Переменные для энкодеров
    EncoderData encoder_data;
    uint32_t last_encoder_update = 0;
    const uint32_t ENCODER_UPDATE_INTERVAL = 20;  // Обновление каждые 20мс (50 Гц)
    
    // Основной цикл
    while (1) {
        // Обработка входящих команд
        Communication_Process();
        
        // Получаем команду движения
        MovementCommand cmd = Communication_GetMovementCommand();
        if (cmd.is_valid) {
            // Применяем команду к моторам
            MotorControl_SetVelocity(cmd.linear_x, cmd.angular_z);
        }
        
        // Обновление данных энкодеров
        uint32_t current_time = HAL_GetTick();
        if (current_time - last_encoder_update >= ENCODER_UPDATE_INTERVAL) {
            // Читаем энкодеры
            encoder_data.encoder_left = EncoderReader_GetLeftCount();
            encoder_data.encoder_right = EncoderReader_GetRightCount();
            encoder_data.timestamp_ms = current_time;
            
            // Отправляем данные энкодера на ROS2
            Communication_SendEncoderData(&encoder_data);
            
            last_encoder_update = current_time;
        }
        
        // Небольшая задержка для снижения нагрузки на CPU
        HAL_Delay(1);
    }
    
    return 0;
}

/**
 * @brief Обработчик прерывания UART RX (рекомендуемый способ)
 * 
 * Это более эффективный способ, чем polling в Communication_Process()
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART1) {
        // Данные получены, они будут обработаны в Communication_Process()
        // или можно обрабатывать здесь напрямую
        Communication_Process();
        
        // Готовим следующий прием (если используем DMA или IT режим)
        // HAL_UART_Receive_IT(&huart1, rx_buffer, 1);
    }
}

