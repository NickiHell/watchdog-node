/**
 * @file communication.c
 * @brief Реализация протокола связи с ROS2
 */

#include "communication.h"
#include "main.h"
#include <string.h>

// Зависимости от HAL
extern UART_HandleTypeDef huart1;  // Предполагаем UART1

// Буферы для приема и передачи
static uint8_t rx_buffer[MAX_PACKET_SIZE];
static uint16_t rx_index = 0;
static uint8_t tx_buffer[MAX_PACKET_SIZE];

// Последняя полученная команда движения
static MovementCommand last_movement_cmd = {0.0f, 0.0f, false};

// Флаг готовности данных
static bool data_ready = false;

/**
 * @brief Инициализация коммуникации
 */
void Communication_Init(void) {
    rx_index = 0;
    memset(rx_buffer, 0, sizeof(rx_buffer));
    last_movement_cmd.is_valid = false;
    data_ready = false;
    
    // Инициализация UART должна быть выполнена в main.c
    // Здесь только сброс внутренних переменных
}

/**
 * @brief Обработка входящих данных
 * Вызывать периодически из main loop или в прерывании UART RX
 */
void Communication_Process(void) {
    // Проверяем наличие данных в UART
    // В реальном проекте это делается через прерывание или DMA
    
    // Пример для polling (не рекомендуется для продакшена):
    uint8_t byte;
    while (HAL_UART_Receive(&huart1, &byte, 1, 0) == HAL_OK) {
        // Добавляем байт в буфер
        if (rx_index < MAX_PACKET_SIZE) {
            rx_buffer[rx_index++] = byte;
            
            // Проверяем начало пакета
            if (rx_index >= 2) {
                if (rx_buffer[0] == PROTOCOL_HEADER_1 && 
                    rx_buffer[1] == PROTOCOL_HEADER_2) {
                    // Нашли начало пакета, проверяем длину
                    if (rx_index >= 4) {
                        uint8_t cmd_type = rx_buffer[2];
                        uint16_t expected_size = 4;  // Минимальный размер
                        
                        if (cmd_type == CMD_MOVEMENT) {
                            expected_size = MOVEMENT_CMD_SIZE;
                        }
                        
                        // Если получили полный пакет
                        if (rx_index >= expected_size) {
                            // Проверяем контрольную сумму
                            uint8_t received_checksum = rx_buffer[expected_size - 1];
                            uint8_t calculated_checksum = Communication_CalculateChecksum(
                                rx_buffer, expected_size - 1);
                            
                            if (received_checksum == calculated_checksum) {
                                // Обрабатываем команду
                                if (cmd_type == CMD_MOVEMENT) {
                                    // Декодируем команду движения
                                    float linear_x, angular_z;
                                    memcpy(&linear_x, &rx_buffer[3], sizeof(float));
                                    memcpy(&angular_z, &rx_buffer[7], sizeof(float));
                                    
                                    last_movement_cmd.linear_x = linear_x;
                                    last_movement_cmd.angular_z = angular_z;
                                    last_movement_cmd.is_valid = true;
                                    data_ready = true;
                                    
                                    // Отправляем подтверждение
                                    Communication_SendSuccess();
                                } else if (cmd_type == CMD_STATUS_REQUEST) {
                                    // Запрос состояния - отправляем данные энкодеров
                                    // (вызывается из main.c после получения запроса)
                                }
                            } else {
                                // Ошибка контрольной суммы
                                Communication_SendError(0x01);  // Error: Invalid checksum
                            }
                            
                            // Очищаем буфер
                            rx_index = 0;
                            memset(rx_buffer, 0, sizeof(rx_buffer));
                        }
                    }
                } else {
                    // Неверный заголовок, ищем начало пакета
                    // Сдвигаем буфер влево
                    for (uint16_t i = 1; i < rx_index; i++) {
                        rx_buffer[i - 1] = rx_buffer[i];
                    }
                    rx_index--;
                }
            }
        } else {
            // Переполнение буфера
            rx_index = 0;
            memset(rx_buffer, 0, sizeof(rx_buffer));
            Communication_SendError(0x02);  // Error: Buffer overflow
        }
    }
}

/**
 * @brief Получить последнюю команду движения
 */
MovementCommand Communication_GetMovementCommand(void) {
    MovementCommand cmd = last_movement_cmd;
    last_movement_cmd.is_valid = false;  // Сбрасываем флаг после чтения
    return cmd;
}

/**
 * @brief Отправить данные энкодеров
 */
void Communication_SendEncoderData(const EncoderData *data) {
    if (data == NULL) return;
    
    uint16_t index = 0;
    
    // Заголовок
    tx_buffer[index++] = PROTOCOL_HEADER_1;
    tx_buffer[index++] = PROTOCOL_HEADER_2;
    
    // Тип ответа
    tx_buffer[index++] = RESP_ENCODER_DATA;
    
    // Данные энкодеров
    memcpy(&tx_buffer[index], &data->encoder_left, sizeof(int32_t));
    index += sizeof(int32_t);
    memcpy(&tx_buffer[index], &data->encoder_right, sizeof(int32_t));
    index += sizeof(int32_t);
    memcpy(&tx_buffer[index], &data->timestamp_ms, sizeof(uint32_t));
    index += sizeof(uint32_t);
    
    // Контрольная сумма
    uint8_t checksum = Communication_CalculateChecksum(tx_buffer, index);
    tx_buffer[index++] = checksum;
    
    // Отправка через UART
    HAL_UART_Transmit(&huart1, tx_buffer, index, 100);
}

/**
 * @brief Отправить ответ об успехе
 */
void Communication_SendSuccess(void) {
    uint16_t index = 0;
    
    tx_buffer[index++] = PROTOCOL_HEADER_1;
    tx_buffer[index++] = PROTOCOL_HEADER_2;
    tx_buffer[index++] = RESP_SUCCESS;
    
    uint8_t checksum = Communication_CalculateChecksum(tx_buffer, index);
    tx_buffer[index++] = checksum;
    
    HAL_UART_Transmit(&huart1, tx_buffer, index, 100);
}

/**
 * @brief Отправить ответ об ошибке
 */
void Communication_SendError(uint8_t error_code) {
    uint16_t index = 0;
    
    tx_buffer[index++] = PROTOCOL_HEADER_1;
    tx_buffer[index++] = PROTOCOL_HEADER_2;
    tx_buffer[index++] = RESP_ERROR;
    tx_buffer[index++] = error_code;
    
    uint8_t checksum = Communication_CalculateChecksum(tx_buffer, index);
    tx_buffer[index++] = checksum;
    
    HAL_UART_Transmit(&huart1, tx_buffer, index, 100);
}

/**
 * @brief Вычисление контрольной суммы (XOR всех байт)
 */
uint8_t Communication_CalculateChecksum(const uint8_t *data, uint16_t length) {
    uint8_t checksum = 0;
    for (uint16_t i = 0; i < length; i++) {
        checksum ^= data[i];
    }
    return checksum;
}
