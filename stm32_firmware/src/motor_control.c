/**
 * @file motor_control.c
 * @brief Реализация управления моторами
 */

#include "motor_control.h"
#include "main.h"
#include <math.h>

// Зависимости от HAL
extern TIM_HandleTypeDef htim2;  // PWM для левого мотора
extern TIM_HandleTypeDef htim3;  // PWM для правого мотора

// Параметры робота
#define WHEEL_BASE 0.25f        // Расстояние между колесами (метры)
#define WHEEL_RADIUS 0.05f      // Радиус колеса (метры)
#define MAX_PWM_VALUE 1000      // Максимальное значение PWM (зависит от настроек таймера)

// Максимальные скорости
static float max_linear_velocity = 0.5f;   // м/с
static float max_angular_velocity = 1.0f;  // рад/с

// Текущая команда
static VelocityCommand current_command = {0.0f, 0.0f};

// Конвертация скорости в PWM
static int16_t velocity_to_pwm(float velocity) {
    // velocity в м/с
    // Конвертируем в об/мин колеса
    float wheel_rpm = (velocity / (2.0f * 3.14159f * WHEEL_RADIUS)) * 60.0f;
    
    // Предполагаем максимальную скорость колеса 100 об/мин при max PWM
    float max_wheel_rpm = 100.0f;
    
    // Нормализуем и ограничиваем
    float pwm_float = (wheel_rpm / max_wheel_rpm) * MAX_PWM_VALUE;
    
    if (pwm_float > MAX_PWM_VALUE) pwm_float = MAX_PWM_VALUE;
    if (pwm_float < -MAX_PWM_VALUE) pwm_float = -MAX_PWM_VALUE;
    
    return (int16_t)pwm_float;
}

void MotorControl_Init(void) {
    // Инициализация таймеров должна быть выполнена в main.c через STM32CubeMX
    // Здесь только сброс переменных
    
    current_command.linear_velocity = 0.0f;
    current_command.angular_velocity = 0.0f;
    
    // Останавливаем моторы
    MotorControl_Stop();
}

void MotorControl_SetVelocity(float linear_x, float angular_z) {
    // Ограничиваем скорости
    if (linear_x > max_linear_velocity) linear_x = max_linear_velocity;
    if (linear_x < -max_linear_velocity) linear_x = -max_linear_velocity;
    if (angular_z > max_angular_velocity) angular_z = max_angular_velocity;
    if (angular_z < -max_angular_velocity) angular_z = -max_angular_velocity;
    
    // Сохраняем команду
    current_command.linear_velocity = linear_x;
    current_command.angular_velocity = angular_z;
    
    // Вычисляем скорости колес по модели дифференциального привода
    // v_left = v_linear - (v_angular * wheel_base / 2)
    // v_right = v_linear + (v_angular * wheel_base / 2)
    float v_left = linear_x - (angular_z * WHEEL_BASE / 2.0f);
    float v_right = linear_x + (angular_z * WHEEL_BASE / 2.0f);
    
    // Конвертируем в PWM
    int16_t pwm_left = velocity_to_pwm(v_left);
    int16_t pwm_right = velocity_to_pwm(v_right);
    
    // Управление левым мотором
    if (pwm_left > 0) {
        // Движение вперед
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_SET);   // IN1
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_RESET); // IN2
        __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, (uint32_t)abs(pwm_left));
    } else if (pwm_left < 0) {
        // Движение назад
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_RESET); // IN1
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_SET);   // IN2
        __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, (uint32_t)abs(pwm_left));
    } else {
        // Остановка
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, GPIO_PIN_RESET);
        __HAL_TIM_SET_COMPARE(&htim2, TIM_CHANNEL_1, 0);
    }
    
    // Управление правым мотором
    if (pwm_right > 0) {
        // Движение вперед
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_3, GPIO_PIN_SET);   // IN1
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET); // IN2
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, (uint32_t)abs(pwm_right));
    } else if (pwm_right < 0) {
        // Движение назад
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_3, GPIO_PIN_RESET); // IN1
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_SET);   // IN2
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, (uint32_t)abs(pwm_right));
    } else {
        // Остановка
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_3, GPIO_PIN_RESET);
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_4, GPIO_PIN_RESET);
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, 0);
    }
}

void MotorControl_Stop(void) {
    MotorControl_SetVelocity(0.0f, 0.0f);
}

VelocityCommand MotorControl_GetCurrentCommand(void) {
    return current_command;
}

void MotorControl_SetMaxVelocities(float max_linear, float max_angular) {
    max_linear_velocity = max_linear;
    max_angular_velocity = max_angular;
}

