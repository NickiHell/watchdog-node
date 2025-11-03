/**
 * @file encoder_reader.c
 * @brief Реализация чтения энкодеров
 */

#include "encoder_reader.h"
#include "main.h"

// Зависимости от HAL
extern TIM_HandleTypeDef htim4;  // Таймер для левого энкодера (TIM4)
extern TIM_HandleTypeDef htim5;  // Таймер для правого энкодера (TIM5)

// Состояние
static int32_t encoder_left_offset = 0;
static int32_t encoder_right_offset = 0;

void EncoderReader_Init(void) {
    // Инициализация таймеров в режиме энкодера должна быть выполнена в main.c
    
    // Сбрасываем смещения
    encoder_left_offset = 0;
    encoder_right_offset = 0;
    
    // Считываем текущие значения как смещение
    encoder_left_offset = (int32_t)__HAL_TIM_GET_COUNTER(&htim4);
    encoder_right_offset = (int32_t)__HAL_TIM_GET_COUNTER(&htim5);
}

EncoderData EncoderReader_GetData(void) {
    EncoderData data;
    
    // Считываем значения таймеров
    // Таймеры настроены в режиме энкодера и автоматически считают
    int32_t left_raw = (int32_t)__HAL_TIM_GET_COUNTER(&htim4);
    int32_t right_raw = (int32_t)__HAL_TIM_GET_COUNTER(&htim5);
    
    // Применяем смещение (для обнуления в начале)
    data.encoder_left = left_raw - encoder_left_offset;
    data.encoder_right = right_raw - encoder_right_offset;
    
    // Получаем временную метку
    data.timestamp_ms = HAL_GetTick();
    
    return data;
}

void EncoderReader_Reset(void) {
    // Сохраняем текущие значения как новые смещения
    encoder_left_offset = (int32_t)__HAL_TIM_GET_COUNTER(&htim4);
    encoder_right_offset = (int32_t)__HAL_TIM_GET_COUNTER(&htim5);
}

int32_t EncoderReader_GetLeftCount(void) {
    EncoderData data = EncoderReader_GetData();
    return data.encoder_left;
}

int32_t EncoderReader_GetRightCount(void) {
    EncoderData data = EncoderReader_GetData();
    return data.encoder_right;
}

