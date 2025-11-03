"""ROS2 узел для обработки речи и голосовых команд."""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist
import threading
import time

from watchdog_speech.speech_recognition import SpeechRecognizer
from watchdog_speech.voice_verification import VoiceVerifier
from watchdog_speech.speech_synthesis import SpeechSynthesizer
from watchdog_speech.audio_capture import AudioCapture
from watchdog_speech.command_processor import CommandProcessor


class SpeechNode(Node):
    """ROS2 узел для обработки речи."""

    def __init__(self):
        super().__init__('speech_node')

        # Параметры
        self.declare_parameter('recognition.model', 'vosk')
        self.declare_parameter('recognition.model_path', '')
        self.declare_parameter('recognition.language', 'ru')
        self.declare_parameter('voice_verification.enabled', True)
        self.declare_parameter('voice_verification.voice_sample_path', '')
        self.declare_parameter('voice_verification.threshold', 0.7)
        self.declare_parameter('synthesis.model', 'silero')
        self.declare_parameter('synthesis.model_id', 'ru_v3')
        self.declare_parameter('synthesis.speaker', 'aidar')
        self.declare_parameter('synthesis.device', 'cpu')
        self.declare_parameter('audio.sample_rate', 16000)
        self.declare_parameter('audio.listen_mode', 'continuous')  # continuous или push_to_talk
        self.declare_parameter('audio.silence_threshold', 0.01)

        # Инициализация компонентов
        self._init_components()

        # Издатели
        self.recognized_text_pub = self.create_publisher(String, '/speech/recognized_text', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.verification_status_pub = self.create_publisher(String, '/speech/verification_status', 10)

        # Подписчики
        self.synthesis_request_sub = self.create_subscription(
            String,
            '/speech/synthesis_request',
            self.synthesis_request_callback,
            10
        )

        # Состояние
        self.is_listening = False
        self.listen_thread = None
        self.last_command_time = 0.0
        self.command_timeout = 2.0  # Таймаут команды движения в секундах

        # Таймеры
        self.create_timer(0.1, self.update_timer_callback)

        # Запускаем прослушивание, если в режиме continuous
        listen_mode = self.get_parameter('audio.listen_mode').get_parameter_value().string_value
        if listen_mode == 'continuous':
            self.start_listening()

        self.get_logger().info('Speech node запущен')

    def _init_components(self):
        """Инициализирует компоненты распознавания, верификации и синтеза."""
        # Распознавание речи
        rec_model = self.get_parameter('recognition.model').get_parameter_value().string_value
        rec_model_path = self.get_parameter('recognition.model_path').get_parameter_value().string_value
        rec_language = self.get_parameter('recognition.language').get_parameter_value().string_value

        try:
            self.speech_recognizer = SpeechRecognizer(
                model_type=rec_model,
                model_path=rec_model_path if rec_model_path else None,
                language=rec_language
            )
        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации распознавания речи: {e}')
            self.speech_recognizer = None

        # Верификация голоса
        verification_enabled = self.get_parameter('voice_verification.enabled').get_parameter_value().bool_value
        voice_sample_path = self.get_parameter('voice_verification.voice_sample_path').get_parameter_value().string_value
        verification_threshold = self.get_parameter('voice_verification.threshold').get_parameter_value().double_value

        if verification_enabled:
            try:
                self.voice_verifier = VoiceVerifier(
                    voice_sample_path=voice_sample_path if voice_sample_path else None,
                    threshold=verification_threshold
                )
                if voice_sample_path:
                    self.voice_verifier.load_reference_voice(voice_sample_path)
            except Exception as e:
                self.get_logger().warn(f'Верификация голоса недоступна: {e}')
                self.voice_verifier = None
        else:
            self.voice_verifier = None
            self.get_logger().info('Верификация голоса отключена')

        # Синтез речи
        synth_model = self.get_parameter('synthesis.model').get_parameter_value().string_value
        synth_model_id = self.get_parameter('synthesis.model_id').get_parameter_value().string_value
        synth_speaker = self.get_parameter('synthesis.speaker').get_parameter_value().string_value
        synth_device = self.get_parameter('synthesis.device').get_parameter_value().string_value

        try:
            self.speech_synthesizer = SpeechSynthesizer(
                model_type=synth_model,
                model_id=synth_model_id,
                speaker=synth_speaker,
                device=synth_device
            )
        except Exception as e:
            self.get_logger().warn(f'Синтез речи недоступен: {e}')
            self.speech_synthesizer = None

        # Захват аудио
        sample_rate = self.get_parameter('audio.sample_rate').get_parameter_value().integer_value
        try:
            self.audio_capture = AudioCapture(sample_rate=sample_rate)
        except Exception as e:
            self.get_logger().error(f'Ошибка инициализации захвата аудио: {e}')
            self.audio_capture = None

        # Процессор команд
        self.command_processor = CommandProcessor()

    def start_listening(self):
        """Начинает прослушивание микрофона."""
        if self.is_listening:
            return

        if not self.audio_capture:
            self.get_logger().error('Захват аудио не инициализирован')
            return

        self.is_listening = True
        self.audio_capture.start_recording()
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        self.get_logger().info('Прослушивание микрофона начато')

    def stop_listening(self):
        """Останавливает прослушивание."""
        self.is_listening = False
        if self.audio_capture:
            self.audio_capture.stop_recording()
        self.get_logger().info('Прослушивание микрофона остановлено')

    def _listen_loop(self):
        """Основной цикл прослушивания."""
        silence_threshold = self.get_parameter('audio.silence_threshold').get_parameter_value().double_value

        while self.is_listening:
            try:
                # Записываем до тишины
                audio_data = self.audio_capture.record_until_silence(
                    silence_threshold=silence_threshold,
                    min_duration=0.5,
                    max_duration=5.0,
                    silence_duration=1.0
                )

                if len(audio_data) < 1600:  # Минимум ~0.1 секунды при 16kHz
                    continue

                # Проверяем голос, если верификация включена
                if self.voice_verifier and self.voice_verifier.model:
                    is_verified, confidence = self.voice_verifier.verify(audio_data)
                    status_msg = String()
                    status_msg.data = f'verified:{confidence:.3f}' if is_verified else f'rejected:{confidence:.3f}'
                    self.verification_status_pub.publish(status_msg)

                    if not is_verified:
                        self.get_logger().warn(f'Голос не верифицирован (confidence={confidence:.3f})')
                        # Можно произнести ответ
                        if self.speech_synthesizer:
                            self.speech_synthesizer.speak('Голос не распознан. Доступ запрещен.')
                        continue

                # Распознаем речь
                if self.speech_recognizer:
                    text = self.speech_recognizer.recognize(audio_data)
                    if text:
                        self.get_logger().info(f'Распознано: "{text}"')

                        # Публикуем распознанный текст
                        text_msg = String()
                        text_msg.data = text
                        self.recognized_text_pub.publish(text_msg)

                        # Обрабатываем команду
                        self.process_voice_command(text)

            except Exception as e:
                self.get_logger().error(f'Ошибка в цикле прослушивания: {e}')

    def process_voice_command(self, text: str):
        """Обрабатывает голосовую команду.

        Args:
            text: Распознанный текст
        """
        command = self.command_processor.process_command(text)

        if not command:
            return

        action = command['action']
        params = command['params']

        if action == 'move':
            # Команда движения
            cmd_vel = Twist()
            cmd_vel.linear.x = params.get('linear_x', 0.0)
            cmd_vel.angular.z = params.get('angular_z', 0.0)
            self.cmd_vel_pub.publish(cmd_vel)
            self.last_command_time = time.time()

            # Подтверждение
            if self.speech_synthesizer:
                self.speech_synthesizer.speak('Выполняю')

        elif action == 'stop':
            # Остановка
            cmd_vel = Twist()
            self.cmd_vel_pub.publish(cmd_vel)
            self.last_command_time = 0.0

            if self.speech_synthesizer:
                self.speech_synthesizer.speak('Останавливаюсь')

        elif action == 'follow':
            # Режим следования (нужно реализовать в контроллере)
            if self.speech_synthesizer:
                self.speech_synthesizer.speak('Следую за вами')

        elif action == 'idle':
            # Режим ожидания
            if self.speech_synthesizer:
                self.speech_synthesizer.speak('Перехожу в режим ожидания')

        elif action == 'greet':
            # Приветствие
            if self.speech_synthesizer:
                self.speech_synthesizer.speak('Привет! Я готов выполнять ваши команды')

    def synthesis_request_callback(self, msg: String):
        """Обработчик запросов на синтез речи.

        Args:
            msg: Текст для синтеза
        """
        if self.speech_synthesizer:
            self.speech_synthesizer.speak(msg.data)
        else:
            self.get_logger().warn('Синтез речи недоступен')

    def update_timer_callback(self):
        """Таймер для остановки команды движения при таймауте."""
        if self.last_command_time > 0:
            elapsed = time.time() - self.last_command_time
            if elapsed > self.command_timeout:
                cmd_vel = Twist()
                self.cmd_vel_pub.publish(cmd_vel)
                self.last_command_time = 0.0

    def destroy_node(self):
        """Очистка при завершении узла."""
        self.stop_listening()
        super().destroy_node()


def main(args=None):
    """Точка входа."""
    rclpy.init(args=args)
    node = SpeechNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

