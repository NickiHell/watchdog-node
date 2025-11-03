/**
 * @file encoder_reader.h
 * @brief Чтение данных энкодеров
 */

#ifndef ENCODER_READER_H
#define ENCODER_READER_H

#include <stdint.h>

// Данные энкодеров
typedef struct {
    int32_t encoder_left;   // Тики левого энкодера
    int32_t encoder_right;  // Тики правого энкодера
    uint32_t timestamp_ms;  // Временная метка в миллисекундах
} EncoderData;

// Инициализация энкодеров
void EncoderReader_Init(void);

// Получить данные энкодеров
EncoderData EncoderReader_GetData(void);

// Сброс счетчиков энкодеров
void EncoderReader_Reset(void);

// Получить тики левого энкодера
int32_t EncoderReader_GetLeftCount(void);

// Получить тики правого энкодера
int32_t EncoderReader_GetRightCount(void);

#endif // ENCODER_READER_H

