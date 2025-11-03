/**
 * @file motor_control.h
 * @brief Управление моторами через PWM и GPIO
 */

#ifndef MOTOR_CONTROL_H
#define MOTOR_CONTROL_H

#include <stdint.h>
#include <stdbool.h>

// Параметры мотора
typedef struct {
    float linear_velocity;   // Линейная скорость (м/с)
    float angular_velocity;  // Угловая скорость (рад/с)
} VelocityCommand;

// Инициализация управления моторами
void MotorControl_Init(void);

// Установка скорости движения
void MotorControl_SetVelocity(float linear_x, float angular_z);

// Остановка моторов
void MotorControl_Stop(void);

// Получение текущей команды скорости
VelocityCommand MotorControl_GetCurrentCommand(void);

// Установка максимальных скоростей
void MotorControl_SetMaxVelocities(float max_linear, float max_angular);

#endif // MOTOR_CONTROL_H

