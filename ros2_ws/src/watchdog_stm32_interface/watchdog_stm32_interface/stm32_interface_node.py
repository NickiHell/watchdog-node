"""ROS2 узел для связи со STM32 микроконтроллером.

Этот узел:
- Подписывается на /cmd_vel для получения команд движения
- Отправляет команды на STM32 через последовательный порт
- Читает данные энкодеров от STM32
- Публикует odometry данные на основе энкодеров
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
import time
import math
from collections import deque

from watchdog_stm32_interface.protocol import (
    STM32Protocol,
    ProtocolError,
    ResponseType,
    CommandType,
)
from watchdog_stm32_interface.serial_interface import SerialInterface


class STM32InterfaceNode(Node):
    """ROS2 узел для интерфейса STM32."""

    def __init__(self):
        super().__init__('stm32_interface_node')

        # Параметры
        self.declare_parameter('port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('timeout', 0.1)
        self.declare_parameter('cmd_vel_timeout', 0.5)  # Таймаут для остановки при отсутствии команд
        self.declare_parameter('encoder_rate', 50.0)  # Частота чтения энкодеров (Гц)
        self.declare_parameter('wheel_radius', 0.05)  # Радиус колеса в метрах
        self.declare_parameter('wheel_base', 0.25)  # Расстояние между колесами в метрах
        self.declare_parameter('encoder_resolution', 360)  # Тиков энкодера на оборот

        port = self.get_parameter('port').get_parameter_value().string_value
        baudrate = self.get_parameter('baudrate').get_parameter_value().integer_value
        timeout = self.get_parameter('timeout').get_parameter_value().double_value

        # Инициализация последовательного порта
        self.serial = SerialInterface(port, baudrate, timeout)

        # Переменные состояния
        self.last_cmd_vel_time = 0.0
        self.cmd_vel_timeout = self.get_parameter('cmd_vel_timeout').get_parameter_value().double_value
        self.last_encoder_left = 0
        self.last_encoder_right = 0
        self.encoder_left = 0
        self.encoder_right = 0
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_encoder_time = time.time()

        # Буфер для неполных пакетов
        self.rx_buffer = bytearray()

        # Издатели
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.status_pub = self.create_publisher(String, '/stm32/status', 10)

        # Подписчики
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # Таймеры
        encoder_rate = self.get_parameter('encoder_rate').get_parameter_value().double_value
        self.create_timer(1.0 / encoder_rate, self.read_encoders_timer_callback)
        self.create_timer(0.1, self.send_commands_timer_callback)

        # Подключение к STM32
        if self.serial.connect():
            self.get_logger().info('STM32 интерфейс запущен')
            self.publish_status('connected')
        else:
            self.get_logger().error('Не удалось подключиться к STM32')
            self.publish_status('disconnected')

    def cmd_vel_callback(self, msg: Twist):
        """Обработчик команд движения.

        Args:
            msg: Сообщение Twist с командами движения
        """
        self.last_cmd_vel_time = time.time()

        # Кодируем команду движения
        command = STM32Protocol.encode_movement_command(msg.linear.x, msg.angular.z)

        # Отправляем команду
        if self.serial.send_command(command):
            self.get_logger().debug(
                f'Отправлена команда: linear={msg.linear.x:.3f}, angular={msg.angular.z:.3f}'
            )
        else:
            self.get_logger().warn('Не удалось отправить команду движения')

    def send_commands_timer_callback(self):
        """Таймер для отправки команд.

        Отправляет команду остановки, если не было команд движения в течение таймаута.
        """
        current_time = time.time()
        time_since_last_cmd = current_time - self.last_cmd_vel_time

        # Если долго не было команд, отправляем команду остановки
        if time_since_last_cmd > self.cmd_vel_timeout:
            if self.last_cmd_vel_time > 0:  # Только если была хотя бы одна команда
                stop_command = STM32Protocol.encode_movement_command(0.0, 0.0)
                self.serial.send_command(stop_command)
                self.last_cmd_vel_time = 0.0  # Сбрасываем, чтобы не спамить

    def read_encoders_timer_callback(self):
        """Таймер для чтения данных энкодеров."""
        # Читаем все доступные данные
        data = self.serial.read_available()
        if data:
            self.rx_buffer.extend(data)
            self.process_rx_buffer()

        # Обновляем odometry
        self.update_odometry()

        # Отправляем запрос состояния (для получения энкодеров)
        status_request = STM32Protocol.encode_status_request()
        self.serial.send_command(status_request)

    def process_rx_buffer(self):
        """Обрабатывает буфер приема, извлекая полные пакеты."""
        while len(self.rx_buffer) >= 4:  # Минимальный размер пакета
            # Ищем начало пакета
            start_pos = STM32Protocol.find_packet_start(bytes(self.rx_buffer))
            if start_pos is None:
                # Начало пакета не найдено, очищаем буфер
                if len(self.rx_buffer) > 100:  # Защита от переполнения
                    self.get_logger().warn('Буфер переполнен, очистка')
                    self.rx_buffer.clear()
                break

            # Удаляем данные до начала пакета
            if start_pos > 0:
                self.rx_buffer = self.rx_buffer[start_pos:]

            # Проверяем, достаточно ли данных для полного пакета
            # Минимальный пакет: заголовок (2) + тип (1) + данные (0+) + чексумма (1) = 4+
            if len(self.rx_buffer) < 4:
                break

            response_type = self.rx_buffer[2]
            # Для ENCODER_DATA: заголовок(2) + тип(1) + данные(12) + чексумма(1) = 16
            min_packet_size = 4
            if response_type == ResponseType.ENCODER_DATA:
                min_packet_size = 16  # encoder_left(4) + encoder_right(4) + timestamp(4)

            if len(self.rx_buffer) < min_packet_size:
                break  # Ждем больше данных

            # Пытаемся декодировать пакет
            try:
                # Для ENCODER_DATA знаем размер, для других - пробуем минимальный
                packet_size = min_packet_size if response_type == ResponseType.ENCODER_DATA else 4
                response_data = bytes(self.rx_buffer[:packet_size])
                response = STM32Protocol.decode_response(response_data)

                # Удаляем обработанный пакет из буфера
                self.rx_buffer = self.rx_buffer[packet_size:]

                # Обрабатываем ответ
                self.handle_response(response)

            except ProtocolError as e:
                self.get_logger().warn(f'Ошибка протокола: {e}')
                # Пропускаем один байт и пробуем снова
                if len(self.rx_buffer) > 1:
                    self.rx_buffer = self.rx_buffer[1:]
                else:
                    break
            except Exception as e:
                self.get_logger().error(f'Ошибка обработки пакета: {e}')
                if len(self.rx_buffer) > 1:
                    self.rx_buffer = self.rx_buffer[1:]
                else:
                    break

    def handle_response(self, response: dict):
        """Обрабатывает ответ от STM32.

        Args:
            response: Словарь с декодированными данными ответа
        """
        response_type = response['type']

        if response_type == ResponseType.ENCODER_DATA:
            parsed = response.get('parsed_data', {})
            self.encoder_left = parsed.get('encoder_left', 0)
            self.encoder_right = parsed.get('encoder_right', 0)
            self.get_logger().debug(
                f'Энкодеры: left={self.encoder_left}, right={self.encoder_right}'
            )

        elif response_type == ResponseType.SUCCESS:
            self.get_logger().debug('Команда выполнена успешно')

        elif response_type == ResponseType.ERROR:
            error_code = response.get('parsed_data', {}).get('error_code', 0)
            self.get_logger().warn(f'Ошибка от STM32: код {error_code}')

    def update_odometry(self):
        """Обновляет odometry на основе данных энкодеров."""
        wheel_radius = self.get_parameter('wheel_radius').get_parameter_value().double_value
        wheel_base = self.get_parameter('wheel_base').get_parameter_value().double_value
        encoder_resolution = self.get_parameter('encoder_resolution').get_parameter_value().integer_value

        # Вычисляем разницу энкодеров
        delta_left = self.encoder_left - self.last_encoder_left
        delta_right = self.encoder_right - self.last_encoder_right

        # Пропускаем обновление если нет изменений
        if delta_left == 0 and delta_right == 0:
            return

        current_time = time.time()
        dt = current_time - self.last_encoder_time
        if dt <= 0:
            return

        # Преобразуем тики в метры
        distance_per_tick = 2.0 * 3.14159 * wheel_radius / encoder_resolution

        # Вычисляем расстояние, пройденное каждым колесом
        dl = delta_left * distance_per_tick
        dr = delta_right * distance_per_tick

        # Вычисляем линейную и угловую скорость
        v = (dr + dl) / 2.0
        w = (dr - dl) / wheel_base

        # Обновляем позицию (простая модель одометрии)
        if abs(w) > 0.001:  # Поворот
            r = v / w
            dtheta = w * dt
            dx = r * (1.0 - abs(dtheta))
            dy = 0.0
        else:  # Прямолинейное движение
            dx = v * dt
            dy = 0.0
            dtheta = 0.0

        # Обновляем глобальную позицию
        self.x += dx * math.cos(self.theta) - dy * math.sin(self.theta)
        self.y += dx * math.sin(self.theta) + dy * math.cos(self.theta)
        self.theta += dtheta

        # Нормализуем угол
        while self.theta > math.pi:
            self.theta -= 2.0 * math.pi
        while self.theta < -math.pi:
            self.theta += 2.0 * math.pi

        # Публикуем odometry
        odom_msg = Odometry()
        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = 'odom'
        odom_msg.child_frame_id = 'base_link'

        # Позиция
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0

        # Ориентация (quaternion из theta)
        odom_msg.pose.pose.orientation.z = math.sin(self.theta / 2.0)
        odom_msg.pose.pose.orientation.w = math.cos(self.theta / 2.0)

        # Скорость
        odom_msg.twist.twist.linear.x = v
        odom_msg.twist.twist.angular.z = w

        self.odom_pub.publish(odom_msg)

        # Обновляем последние значения
        self.last_encoder_left = self.encoder_left
        self.last_encoder_right = self.encoder_right
        self.last_encoder_time = current_time

    def publish_status(self, status: str):
        """Публикует статус соединения.

        Args:
            status: Текст статуса
        """
        msg = String()
        msg.data = status
        self.status_pub.publish(msg)

    def destroy_node(self):
        """Закрывает соединение при завершении узла."""
        self.serial.disconnect()
        super().destroy_node()


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = STM32InterfaceNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

