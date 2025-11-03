"""Модуль обработки голосовых команд."""

import re
from typing import Dict, Optional, Callable
import rclpy
from rclpy.logging import get_logger


class CommandProcessor:
    """Класс для обработки и распознавания голосовых команд."""

    def __init__(self):
        """Инициализирует процессор команд."""
        self.logger = get_logger('CommandProcessor')
        self.commands = self._initialize_commands()

    def _initialize_commands(self) -> Dict[str, Dict]:
        """Инициализирует словарь команд.

        Returns:
            Словарь команд с паттернами и обработчиками
        """
        return {
            'move_forward': {
                'patterns': [
                    r'вперед',
                    r'ехать вперед',
                    r'двигайся вперед',
                    r'поехали вперед',
                    r'вперед поехали',
                ],
                'action': 'move',
                'params': {'linear_x': 0.5, 'angular_z': 0.0},
            },
            'move_backward': {
                'patterns': [
                    r'назад',
                    r'ехать назад',
                    r'двигайся назад',
                    r'поехали назад',
                ],
                'action': 'move',
                'params': {'linear_x': -0.3, 'angular_z': 0.0},
            },
            'turn_left': {
                'patterns': [
                    r'влево',
                    r'налево',
                    r'поверни влево',
                    r'поверни налево',
                    r'поворот влево',
                ],
                'action': 'move',
                'params': {'linear_x': 0.0, 'angular_z': 0.5},
            },
            'turn_right': {
                'patterns': [
                    r'вправо',
                    r'направо',
                    r'поверни вправо',
                    r'поверни направо',
                    r'поворот вправо',
                ],
                'action': 'move',
                'params': {'linear_x': 0.0, 'angular_z': -0.5},
            },
            'stop': {
                'patterns': [
                    r'стоп',
                    r'остановись',
                    r'останови',
                    r'стоп машина',
                    r'стоп робот',
                ],
                'action': 'stop',
                'params': {},
            },
            'follow_me': {
                'patterns': [
                    r'следуй за мной',
                    r'следуй',
                    r'за мной',
                    r'иди за мной',
                ],
                'action': 'follow',
                'params': {},
            },
            'idle_mode': {
                'patterns': [
                    r'режим ожидания',
                    r'простой режим',
                    r'режим простоя',
                    r'жду',
                ],
                'action': 'idle',
                'params': {},
            },
            'hello': {
                'patterns': [
                    r'привет',
                    r'здравствуй',
                    r'здравствуйте',
                ],
                'action': 'greet',
                'params': {},
            },
        }

    def process_command(self, text: str) -> Optional[Dict]:
        """Обрабатывает текст и возвращает команду.

        Args:
            text: Распознанный текст

        Returns:
            Словарь с командой или None:
            {
                'action': str,  # Тип действия
                'params': dict,  # Параметры команды
                'confidence': float,  # Уверенность (0.0-1.0)
            }
        """
        if not text:
            return None

        text_lower = text.lower().strip()

        # Ищем совпадение с паттернами команд
        best_match = None
        best_score = 0.0

        for command_name, command_data in self.commands.items():
            for pattern in command_data['patterns']:
                match = re.search(pattern, text_lower)
                if match:
                    # Вычисляем "схожесть" (длина совпадения / длина текста)
                    match_length = len(match.group())
                    score = match_length / len(text_lower) if text_lower else 0.0

                    if score > best_score:
                        best_score = score
                        best_match = {
                            'action': command_data['action'],
                            'params': command_data['params'].copy(),
                            'confidence': score,
                            'command_name': command_name,
                        }

        if best_match:
            self.logger.info(f'Распознана команда: {best_match["command_name"]} (confidence={best_match["confidence"]:.2f})')
            return best_match

        self.logger.debug(f'Команда не распознана в тексте: "{text}"')
        return None

    def add_custom_command(self, name: str, patterns: list, action: str, params: dict):
        """Добавляет пользовательскую команду.

        Args:
            name: Имя команды
            patterns: Список паттернов для распознавания
            action: Тип действия
            params: Параметры команды
        """
        self.commands[name] = {
            'patterns': patterns,
            'action': action,
            'params': params,
        }
        self.logger.info(f'Добавлена пользовательская команда: {name}')

