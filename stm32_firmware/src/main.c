/**
 * @file main.c
 * @brief Основной файл прошивки STM32 для WatchDog Robot
 * 
 * Управление моторами, чтение энкодеров, коммуникация с ROS2
 */

#include "main.h"
#include "motor_control.h"
#include "encoder_reader.h"
#include "communication.h"
#include <stdio.h>

// Объявления таймеров (генерируются STM32CubeMX)
TIM_HandleTypeDef htim2;  // PWM левого мотора
TIM_HandleTypeDef htim3;  // PWM правого мотора
TIM_HandleTypeDef htim4;  // Энкодер левого мотора
TIM_HandleTypeDef htim5;  // Энкодер правого мотора

// Объявление UART (генерируется STM32CubeMX)
UART_HandleTypeDef huart1;

// Переменные состояния
static uint32_t last_encoder_send = 0;
static const uint32_t ENCODER_SEND_INTERVAL = 20;  // Отправка каждые 20мс (50 Гц)

// Прототипы функций (генерируются STM32CubeMX)
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_TIM2_Init(void);
static void MX_TIM3_Init(void);
static void MX_TIM4_Init(void);
static void MX_TIM5_Init(void);
static void MX_USART1_UART_Init(void);

int main(void) {
    // Инициализация HAL
    HAL_Init();
    
    // Конфигурация системных часов
    SystemClock_Config();
    
    // Инициализация периферии (генерируется STM32CubeMX)
    MX_GPIO_Init();
    MX_USART1_UART_Init();
    MX_TIM2_Init();
    MX_TIM3_Init();
    MX_TIM4_Init();
    MX_TIM5_Init();
    
    // Запуск таймеров
    HAL_TIM_PWM_Start(&htim2, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
    HAL_TIM_Encoder_Start(&htim4, TIM_CHANNEL_ALL);
    HAL_TIM_Encoder_Start(&htim5, TIM_CHANNEL_ALL);
    
    // Инициализация модулей
    MotorControl_Init();
    EncoderReader_Init();
    Communication_Init();
    
    // Основной цикл
    while (1) {
        // Обработка входящих команд
        Communication_Process();
        
        // Получаем команду движения
        MovementCommand cmd = Communication_GetMovementCommand();
        if (cmd.is_valid) {
            MotorControl_SetVelocity(cmd.linear_x, cmd.angular_z);
        }
        
        // Отправка данных энкодеров
        uint32_t current_time = HAL_GetTick();
        if (current_time - last_encoder_send >= ENCODER_SEND_INTERVAL) {
            EncoderData encoder_data = EncoderReader_GetData();
            Communication_SendEncoderData(&encoder_data);
            last_encoder_send = current_time;
        }
        
        // Небольшая задержка
        HAL_Delay(1);
    }
    
    return 0;
}

/**
 * @brief Обработчик прерывания UART RX
 */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart) {
    if (huart->Instance == USART1) {
        // Данные получены, обрабатываются в Communication_Process()
    }
}

/**
 * @brief Обработчик ошибок
 */
void Error_Handler(void) {
    // Остановка моторов при ошибке
    MotorControl_Stop();
    
    // Можно добавить индикацию ошибки (LED и т.д.)
    while (1) {
        HAL_Delay(100);
    }
}

