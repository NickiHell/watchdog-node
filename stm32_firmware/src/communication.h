/**
 * @file communication.h
 * @brief Протокол связи с ROS2 через UART
 * 
 * Реализует протокол обмена данными:
 * - Прием команд движения (cmd_vel)
 * - Отправка данных энкодеров
 * - Обработка запросов состояния
 */

#ifndef COMMUNICATION_H
#define COMMUNICATION_H

#include <stdint.h>
#include <stdbool.h>

// Константы протокола
#define PROTOCOL_HEADER_1     0xAA
#define PROTOCOL_HEADER_2     0x55

// Типы команд
#define CMD_MOVEMENT          0x01
#define CMD_STATUS_REQUEST    0x02
#define CMD_PARAM_SET         0x03

// Типы ответов
#define RESP_ERROR            0x10
#define RESP_SUCCESS          0x11
#define RESP_ENCODER_DATA     0x12

// Размеры пакетов
#define MAX_PACKET_SIZE       64
#define MOVEMENT_CMD_SIZE     16  // заголовок(2) + тип(1) + linear(4) + angular(4) + chksum(1)
#define ENCODER_RESP_SIZE      16  // заголовок(2) + тип(1) + left(4) + right(4) + timestamp(4) + chksum(1)

// Структура команды движения
typedef struct {
    float linear_x;
    float angular_z;
    bool is_valid;
} MovementCommand;

// Структура данных энкодеров
typedef struct {
    int32_t encoder_left;
    int32_t encoder_right;
    uint32_t timestamp_ms;
} EncoderData;

// Инициализация коммуникации
void Communication_Init(void);

// Обработка входящих данных (вызывать периодически)
void Communication_Process(void);

// Получить последнюю команду движения
MovementCommand Communication_GetMovementCommand(void);

// Отправить данные энкодеров
void Communication_SendEncoderData(const EncoderData *data);

// Отправить ответ об успехе
void Communication_SendSuccess(void);

// Отправить ответ об ошибке
void Communication_SendError(uint8_t error_code);

// Вычисление контрольной суммы
uint8_t Communication_CalculateChecksum(const uint8_t *data, uint16_t length);

#endif // COMMUNICATION_H

