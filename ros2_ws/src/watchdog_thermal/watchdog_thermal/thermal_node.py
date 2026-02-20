"""ROS2 узел термоуправления дрона Watchdog.

Аппаратура (RPI 5 GPIO):
  - DS18B20 × 2 (GPIO4, 1-Wire): датчики температуры в корпусе и мачте LiDAR
  - Вентилятор 40 мм IP67 (GPIO18, Hardware PWM): охлаждение корпуса
  - Нагреватель мачты LiDAR 3 Вт (GPIO17, MOSFET): обогрев RPLidar S2 при <0°C

Диапазон: −5...+30°C (pet-project уровень).
  - LiPo при −5°C: ёмкость −10%, без предогрева
  - RPI 5: конформное покрытие от конденсата
  - RPLidar S2 (рабочий диапазон 0°C...40°C): нагрев при < 0°C

Зависимости на RPI 5:
  pip install w1thermsensor
  Включить 1-Wire: /boot/config.txt → dtoverlay=w1-gpio
  Включить PWM: /boot/config.txt → dtoverlay=pwm,pin=18,func=2
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Float32

try:
    from RPi import GPIO

    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False

try:
    from w1thermsensor import W1ThermSensor

    W1_AVAILABLE = True
except ImportError:
    W1_AVAILABLE = False

# Hardware PWM через pigpio (точнее чем RPi.GPIO)
try:
    import pigpio

    PIGPIO_AVAILABLE = True
except ImportError:
    PIGPIO_AVAILABLE = False


class ThermalNode(Node):
    """Термоуправление дрона Watchdog."""

    def __init__(self):
        super().__init__("thermal_node")

        # GPIO пины
        self.declare_parameter("fan_gpio_pin", 18)  # Hardware PWM
        self.declare_parameter("heater_gpio_pin", 17)  # MOSFET gate
        # Пороги вентилятора
        self.declare_parameter("fan_on_temp", 35.0)
        self.declare_parameter("fan_off_temp", 28.0)
        self.declare_parameter("fan_max_duty", 100)  # %
        # Пороги нагревателя мачты (RPLidar S2 работает от 0°C)
        self.declare_parameter("heater_on_temp", 0.0)
        self.declare_parameter("heater_off_temp", 5.0)
        # ID датчиков (пусто = автоопределение)
        self.declare_parameter("sensor_enclosure_id", "")
        self.declare_parameter("sensor_mast_id", "")

        self.fan_pin = self.get_parameter("fan_gpio_pin").value
        self.heater_pin = self.get_parameter("heater_gpio_pin").value
        self.fan_on = self.get_parameter("fan_on_temp").value
        self.fan_off = self.get_parameter("fan_off_temp").value
        self.fan_max_duty = self.get_parameter("fan_max_duty").value
        self.heater_on = self.get_parameter("heater_on_temp").value
        self.heater_off = self.get_parameter("heater_off_temp").value

        # Состояние
        self.temp_enclosure: float | None = None
        self.temp_mast: float | None = None
        self.fan_active = False
        self.heater_active = False
        self.sensors = []

        # GPIO инициализация
        self.pigpio_pi = None
        self._init_gpio()
        self._init_sensors()

        # Публикации
        self.status_pub = self.create_publisher(String, "/thermal/status", 10)
        self.temp_enclosure_pub = self.create_publisher(Float32, "/thermal/temp_enclosure", 10)
        self.temp_mast_pub = self.create_publisher(Float32, "/thermal/temp_mast", 10)

        # Цикл 1 Hz — достаточно для термоуправления
        self.create_timer(1.0, self._thermal_loop)

        self.get_logger().info(
            f"ThermalNode запущен | "
            f"fan GPIO{self.fan_pin} (on>{self.fan_on}°C) | "
            f"heater GPIO{self.heater_pin} (on<{self.heater_on}°C) | "
            f"GPIO={'ok' if GPIO_AVAILABLE else 'STUB'} | "
            f"W1={'ok' if W1_AVAILABLE else 'STUB'}"
        )

    def _init_gpio(self):
        """Инициализирует GPIO для вентилятора (PWM) и нагревателя (MOSFET)."""
        if PIGPIO_AVAILABLE:
            try:
                self.pigpio_pi = pigpio.pi()
                if not self.pigpio_pi.connected:
                    self.pigpio_pi = None
                    self.get_logger().warn("pigpiod не запущен, fallback на RPi.GPIO")
                else:
                    # Hardware PWM на pin 18 (GPIO18 = PWM0)
                    self.pigpio_pi.set_mode(self.fan_pin, pigpio.OUTPUT)
                    self.pigpio_pi.hardware_PWM(self.fan_pin, 25000, 0)  # 25 кГц
                    # Heater как простой цифровой выход
                    self.pigpio_pi.set_mode(self.heater_pin, pigpio.OUTPUT)
                    self.pigpio_pi.write(self.heater_pin, 0)
                    self.get_logger().info("pigpio: Hardware PWM инициализирован")
                    return
            except Exception as e:
                self.get_logger().warn(f"pigpio ошибка: {e}")

        if GPIO_AVAILABLE:
            try:
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.fan_pin, GPIO.OUT)
                GPIO.setup(self.heater_pin, GPIO.OUT)
                self._fan_pwm = GPIO.PWM(self.fan_pin, 25000)
                self._fan_pwm.start(0)
                GPIO.output(self.heater_pin, GPIO.LOW)
                self.get_logger().info("RPi.GPIO: PWM инициализирован (software)")
            except Exception as e:
                self.get_logger().warn(f"GPIO ошибка: {e}")
        else:
            self.get_logger().warn("GPIO недоступен — режим симуляции")

    def _init_sensors(self):
        """Инициализирует DS18B20 датчики через 1-Wire."""
        if not W1_AVAILABLE:
            self.get_logger().warn("w1thermsensor не установлен — температура недоступна")
            return

        try:
            self.sensors = W1ThermSensor.get_available_sensors()
            self.get_logger().info(f"DS18B20 найдено датчиков: {len(self.sensors)}")
            for i, s in enumerate(self.sensors):
                self.get_logger().info(f"  Датчик {i}: id={s.sensor_id}")
        except Exception as e:
            self.get_logger().error(f"Ошибка инициализации DS18B20: {e}")

    def _read_temperatures(self):
        """Читает температуры с DS18B20 датчиков."""
        if not W1_AVAILABLE or not self.sensors:
            # Режим симуляции — возвращаем 20°C
            self.temp_enclosure = 20.0
            self.temp_mast = 20.0
            return

        try:
            if len(self.sensors) >= 1:
                self.temp_enclosure = self.sensors[0].get_temperature()
            if len(self.sensors) >= 2:
                self.temp_mast = self.sensors[1].get_temperature()
            elif len(self.sensors) == 1:
                # Только один датчик — используем для обоих
                self.temp_mast = self.temp_enclosure
        except Exception as e:
            self.get_logger().debug(f"Ошибка чтения температуры: {e}")

    def _set_fan(self, duty_percent: int):
        """Устанавливает скважность вентилятора (0-100%)."""
        duty_percent = max(0, min(self.fan_max_duty, duty_percent))

        if self.pigpio_pi and self.pigpio_pi.connected:
            duty_million = duty_percent * 10000  # pigpio: 0-1000000
            self.pigpio_pi.hardware_PWM(self.fan_pin, 25000, duty_million)
        elif GPIO_AVAILABLE and hasattr(self, "_fan_pwm"):
            self._fan_pwm.ChangeDutyCycle(duty_percent)

        self.fan_active = duty_percent > 0

    def _set_heater(self, on: bool):
        """Включает/выключает нагреватель мачты через MOSFET."""
        if self.pigpio_pi and self.pigpio_pi.connected:
            self.pigpio_pi.write(self.heater_pin, 1 if on else 0)
        elif GPIO_AVAILABLE:
            GPIO.output(self.heater_pin, GPIO.HIGH if on else GPIO.LOW)

        self.heater_active = on

    def _thermal_loop(self):
        """1 Hz: читает температуры и управляет актуаторами."""
        self._read_temperatures()

        # Управление вентилятором (по температуре корпуса)
        if self.temp_enclosure is not None:
            if not self.fan_active and self.temp_enclosure >= self.fan_on:
                self._set_fan(100)
                self.get_logger().info(f"Вентилятор ВКЛ (T={self.temp_enclosure:.1f}°C > {self.fan_on}°C)")
            elif self.fan_active and self.temp_enclosure <= self.fan_off:
                self._set_fan(0)
                self.get_logger().info(f"Вентилятор ВЫКЛ (T={self.temp_enclosure:.1f}°C < {self.fan_off}°C)")
            elif self.fan_active:
                # Пропорциональный PWM: 50-100% в диапазоне fan_off..fan_on+10
                ratio = min(1.0, (self.temp_enclosure - self.fan_off) / 10.0)
                duty = int(50 + ratio * 50)
                self._set_fan(duty)

        # Управление нагревателем мачты (по температуре мачты)
        if self.temp_mast is not None:
            if not self.heater_active and self.temp_mast <= self.heater_on:
                self._set_heater(True)
                self.get_logger().info(f"Нагреватель мачты ВКЛ (T={self.temp_mast:.1f}°C <= {self.heater_on}°C)")
            elif self.heater_active and self.temp_mast >= self.heater_off:
                self._set_heater(False)
                self.get_logger().info(f"Нагреватель мачты ВЫКЛ (T={self.temp_mast:.1f}°C >= {self.heater_off}°C)")

        # Публикуем данные
        self._publish_status()

    def _publish_status(self):
        """Публикует статус термосистемы."""
        if self.temp_enclosure is not None:
            msg = Float32()
            msg.data = float(self.temp_enclosure)
            self.temp_enclosure_pub.publish(msg)

        if self.temp_mast is not None:
            msg = Float32()
            msg.data = float(self.temp_mast)
            self.temp_mast_pub.publish(msg)

        status = String()
        status.data = (
            (
                f"enclosure={self.temp_enclosure:.1f}°C|"
                f"mast={self.temp_mast:.1f}°C|"
                f"fan={'ON' if self.fan_active else 'OFF'}|"
                f"heater={'ON' if self.heater_active else 'OFF'}"
            )
            if self.temp_enclosure is not None
            else "sensors_unavailable"
        )
        self.status_pub.publish(status)

    def destroy_node(self):
        """Корректное завершение — выключаем все актуаторы."""
        try:
            self._set_fan(0)
            self._set_heater(False)
            if self.pigpio_pi and self.pigpio_pi.connected:
                self.pigpio_pi.stop()
            elif GPIO_AVAILABLE:
                GPIO.cleanup()
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = ThermalNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
