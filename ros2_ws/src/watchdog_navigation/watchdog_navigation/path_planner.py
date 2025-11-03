"""Модуль планирования пути на основе карты."""

import numpy as np
from typing import List, Tuple, Optional
from nav_msgs.msg import OccupancyGrid, Path
from geometry_msgs.msg import PoseStamped, Point
import math
import rclpy
from rclpy.logging import get_logger


class PathPlanner:
    """Класс для планирования пути на карте."""

    def __init__(self, inflation_radius: float = 0.3):
        """Инициализирует планировщик пути.

        Args:
            inflation_radius: Радиус раздувания препятствий (метры)
        """
        self.inflation_radius = inflation_radius
        self.logger = get_logger('PathPlanner')

    def plan_path(
        self,
        start: Tuple[float, float],
        goal: Tuple[float, float],
        map_data: np.ndarray,
        map_info: dict
    ) -> Optional[List[Tuple[float, float]]]:
        """Планирует путь от старта до цели.

        Args:
            start: Стартовая позиция (x, y) в метрах
            goal: Целевая позиция (x, y) в метрах
            map_data: 2D массив карты (numpy)
            map_info: Словарь с информацией о карте (origin, resolution)

        Returns:
            Список точек пути [(x, y), ...] или None если путь не найден
        """
        if map_data is None or map_info is None:
            return None

        # Конвертируем мировые координаты в координаты карты
        start_cell = self._world_to_map(start[0], start[1], map_info)
        goal_cell = self._world_to_map(goal[0], goal[1], map_info)

        if not self._is_valid_cell(start_cell, map_data):
            self.logger.warn(f'Стартовая позиция невалидна: {start_cell}')
            return None

        if not self._is_valid_cell(goal_cell, map_data):
            self.logger.warn(f'Целевая позиция невалидна: {goal_cell}')
            return None

        # Простой A* алгоритм
        path = self._astar(start_cell, goal_cell, map_data)

        if path:
            # Конвертируем обратно в мировые координаты
            world_path = [self._map_to_world(cell[0], cell[1], map_info) for cell in path]
            return world_path

        return None

    def _world_to_map(self, x: float, y: float, map_info: dict) -> Tuple[int, int]:
        """Конвертирует мировые координаты в координаты карты.

        Args:
            x: X координата в метрах
            y: Y координата в метрах
            map_info: Информация о карте

        Returns:
            Кортеж (map_x, map_y)
        """
        map_x = int((x - map_info['origin_x']) / map_info['resolution'])
        map_y = int((y - map_info['origin_y']) / map_info['resolution'])
        return (map_x, map_y)

    def _map_to_world(self, map_x: int, map_y: int, map_info: dict) -> Tuple[float, float]:
        """Конвертирует координаты карты в мировые координаты.

        Args:
            map_x: X координата карты
            map_y: Y координата карты
            map_info: Информация о карте

        Returns:
            Кортеж (x, y) в метрах
        """
        x = map_x * map_info['resolution'] + map_info['origin_x']
        y = map_y * map_info['resolution'] + map_info['origin_y']
        return (x, y)

    def _is_valid_cell(self, cell: Tuple[int, int], map_data: np.ndarray) -> bool:
        """Проверяет, является ли ячейка валидной (свободной).

        Args:
            cell: Координаты ячейки (x, y)
            map_data: Данные карты

        Returns:
            True если ячейка свободна
        """
        x, y = cell
        height, width = map_data.shape

        if x < 0 or x >= width or y < 0 or y >= height:
            return False

        # Проверяем препятствия с учетом inflation_radius
        inflation_cells = int(self.inflation_radius / 0.05)  # Предполагаем разрешение ~5см

        for dy in range(-inflation_cells, inflation_cells + 1):
            for dx in range(-inflation_cells, inflation_cells + 1):
                nx, ny = x + dx, y + dy
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    return False

                distance = math.sqrt(dx * dx + dy * dy)
                if distance <= inflation_cells:
                    if map_data[ny, nx] > 50:  # Препятствие
                        return False

        return True

    def _astar(
        self,
        start: Tuple[int, int],
        goal: Tuple[int, int],
        map_data: np.ndarray
    ) -> Optional[List[Tuple[int, int]]]:
        """Реализация алгоритма A* для поиска пути.

        Args:
            start: Стартовая ячейка
            goal: Целевая ячейка
            map_data: Данные карты

        Returns:
            Список ячеек пути или None
        """
        height, width = map_data.shape

        # Структуры для A*
        open_set = {start}
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self._heuristic(start, goal)}

        while open_set:
            # Выбираем узел с минимальным f_score
            current = min(open_set, key=lambda x: f_score.get(x, float('inf')))
            if current == goal:
                # Восстанавливаем путь
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                path.reverse()
                return path

            open_set.remove(current)

            # Проверяем соседей
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)

                if not self._is_valid_cell(neighbor, map_data):
                    continue

                # Вычисляем стоимость перехода (диагональ дороже)
                move_cost = 1.414 if abs(dx) + abs(dy) == 2 else 1.0
                tentative_g_score = g_score[current] + move_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal)
                    open_set.add(neighbor)

        return None  # Путь не найден

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Эвристическая функция для A* (евклидово расстояние).

        Args:
            a: Первая точка
            b: Вторая точка

        Returns:
            Расстояние
        """
        return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

    def simplify_path(self, path: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Упрощает путь, убирая лишние точки.

        Args:
            path: Исходный путь

        Returns:
            Упрощенный путь
        """
        if len(path) <= 2:
            return path

        simplified = [path[0]]

        for i in range(1, len(path) - 1):
            # Проверяем, можно ли убрать точку (прямая линия свободна)
            prev_point = simplified[-1]
            next_point = path[i + 1]

            # Упрощенная проверка - просто пропускаем точки близко к прямой
            dx1 = path[i][0] - prev_point[0]
            dy1 = path[i][1] - prev_point[1]
            dx2 = next_point[0] - prev_point[0]
            dy2 = next_point[1] - prev_point[1]

            # Если точка не сильно отклоняется от прямой, пропускаем её
            cross_product = abs(dx1 * dy2 - dy1 * dx2)
            if cross_product > 0.1:  # Порог
                simplified.append(path[i])

        simplified.append(path[-1])
        return simplified

