"""Модуль 3D планирования пути для дрона."""

import math
from heapq import heappush, heappop


class PathPlanner:
    """Класс для планирования пути в 3D пространстве с использованием алгоритма A*."""

    def __init__(self, inflation_radius: float = 0.5, grid_resolution: float = 0.2):
        """Инициализация планировщика пути.

        Args:
            inflation_radius: Радиус увеличения препятствий (м)
            grid_resolution: Разрешение сетки для A* (м). Меньше значение = точнее, но медленнее
        """
        self.inflation_radius = inflation_radius
        self.grid_resolution = grid_resolution
        self.obstacle_map = None
        self.map_resolution = 0.1  # Разрешение карты (м/пиксель)
        self.map_origin = (0.0, 0.0, 0.0)  # Начало координат карты

        # Направления для поиска соседей (26-связность в 3D)
        self.neighbors_26 = [
            (-1, -1, -1),
            (-1, -1, 0),
            (-1, -1, 1),
            (-1, 0, -1),
            (-1, 0, 0),
            (-1, 0, 1),
            (-1, 1, -1),
            (-1, 1, 0),
            (-1, 1, 1),
            (0, -1, -1),
            (0, -1, 0),
            (0, -1, 1),
            (0, 0, -1),
            (0, 0, 1),
            (0, 1, -1),
            (0, 1, 0),
            (0, 1, 1),
            (1, -1, -1),
            (1, -1, 0),
            (1, -1, 1),
            (1, 0, -1),
            (1, 0, 0),
            (1, 0, 1),
            (1, 1, -1),
            (1, 1, 0),
            (1, 1, 1),
        ]

    def plan_path(
        self,
        start: tuple[float, float, float],
        goal: tuple[float, float, float],
        obstacles: list[tuple[float, float, float]] | None = None,
        max_height: float = 10.0,
    ) -> list[tuple[float, float, float]] | None:
        """Планирует путь от начальной точки к цели с использованием алгоритма A*.

        Args:
            start: Начальная точка (x, y, z)
            goal: Целевая точка (x, y, z)
            obstacles: Список препятствий [(x, y, z, radius), ...] или [(x, y, z), ...]
            max_height: Максимальная высота полета (м)

        Returns:
            Список точек пути или None если путь не найден
        """
        if obstacles is None:
            obstacles = []

        # Проверяем границы высоты
        if start[2] > max_height or goal[2] > max_height:
            return None

        # Быстрая проверка: прямой путь без препятствий
        if self._is_path_clear(start, goal, obstacles):
            return [start, goal]

        # Используем A* для поиска пути
        path = self._astar_path(start, goal, obstacles, max_height)

        if path is None or len(path) == 0:
            return None

        # Упрощаем путь, удаляя лишние точки
        simplified_path = self.simplify_path(path, obstacles)
        return simplified_path

    def _is_path_clear(
        self,
        start: tuple[float, float, float],
        goal: tuple[float, float, float],
        obstacles: list[tuple[float, float, float]],
    ) -> bool:
        """Проверяет, свободен ли путь от препятствий."""
        # Вычисляем направление и расстояние
        dx = goal[0] - start[0]
        dy = goal[1] - start[1]
        dz = goal[2] - start[2]
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)

        # Проверяем, что расстояние достаточно большое для нормализации
        if distance < 0.1 or distance <= 0.0:
            return True

        # Нормализуем направление (защита от деления на ноль)
        if distance > 0.0:
            dx /= distance
            dy /= distance
            dz /= distance
        else:
            return True

        # Проверяем каждое препятствие
        for obstacle in obstacles:
            if len(obstacle) >= 4:
                ox, oy, oz, radius = obstacle[0], obstacle[1], obstacle[2], obstacle[3]
            else:
                ox, oy, oz = obstacle[0], obstacle[1], obstacle[2]
                radius = self.inflation_radius

            # Вычисляем расстояние от линии до препятствия
            # Вектор от start до obstacle
            to_obstacle_x = ox - start[0]
            to_obstacle_y = oy - start[1]
            to_obstacle_z = oz - start[2]

            # Проекция на направление пути
            projection = to_obstacle_x * dx + to_obstacle_y * dy + to_obstacle_z * dz

            # Если проекция вне отрезка, пропускаем
            if projection < 0 or projection > distance:
                continue

            # Точка на линии, ближайшая к препятствию
            closest_x = start[0] + dx * projection
            closest_y = start[1] + dy * projection
            closest_z = start[2] + dz * projection

            # Расстояние от препятствия до линии
            dist_to_line = math.sqrt((ox - closest_x) ** 2 + (oy - closest_y) ** 2 + (oz - closest_z) ** 2)

            if dist_to_line < radius:
                return False

        return True

    def _world_to_grid(self, point: tuple[float, float, float]) -> tuple[int, int, int]:
        """Преобразует мировые координаты в координаты сетки.

        Args:
            point: Точка в мировых координатах (x, y, z)

        Returns:
            Координаты сетки (gx, gy, gz)
        """
        gx = int(round(point[0] / self.grid_resolution))
        gy = int(round(point[1] / self.grid_resolution))
        gz = int(round(point[2] / self.grid_resolution))
        return (gx, gy, gz)

    def _grid_to_world(self, grid_point: tuple[int, int, int]) -> tuple[float, float, float]:
        """Преобразует координаты сетки в мировые координаты.

        Args:
            grid_point: Точка в координатах сетки (gx, gy, gz)

        Returns:
            Точка в мировых координатах (x, y, z)
        """
        x = grid_point[0] * self.grid_resolution
        y = grid_point[1] * self.grid_resolution
        z = grid_point[2] * self.grid_resolution
        return (x, y, z)

    def _heuristic(self, a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
        """Эвристическая функция для A* (евклидово расстояние с учетом высоты).

        Предпочитает горизонтальное движение, но учитывает вертикальное.

        Args:
            a: Первая точка сетки
            b: Вторая точка сетки

        Returns:
            Оценочное расстояние
        """
        dx = a[0] - b[0]
        dy = a[1] - b[1]
        dz = a[2] - b[2]

        # Горизонтальное расстояние важнее вертикального (коэффициент 1.0 vs 1.5)
        horizontal_dist = math.sqrt(dx * dx + dy * dy)
        vertical_dist = abs(dz)

        return horizontal_dist + 1.5 * vertical_dist

    def _is_cell_free(
        self, grid_pos: tuple[int, int, int], obstacles: list[tuple[float, float, float]], max_height: float
    ) -> bool:
        """Проверяет, свободна ли ячейка сетки от препятствий.

        Args:
            grid_pos: Позиция в сетке (gx, gy, gz)
            obstacles: Список препятствий
            max_height: Максимальная высота

        Returns:
            True если ячейка свободна
        """
        world_pos = self._grid_to_world(grid_pos)

        # Проверка границ высоты
        if world_pos[2] < 0 or world_pos[2] > max_height:
            return False

        # Проверка препятствий
        for obstacle in obstacles:
            if len(obstacle) >= 4:
                ox, oy, oz, radius = obstacle[0], obstacle[1], obstacle[2], obstacle[3]
            else:
                ox, oy, oz = obstacle[0], obstacle[1], obstacle[2]
                radius = self.inflation_radius

            # Расстояние от ячейки до препятствия
            dist = math.sqrt((world_pos[0] - ox) ** 2 + (world_pos[1] - oy) ** 2 + (world_pos[2] - oz) ** 2)

            if dist < radius:
                return False

        return True

    def _astar_path(
        self,
        start: tuple[float, float, float],
        goal: tuple[float, float, float],
        obstacles: list[tuple[float, float, float]],
        max_height: float,
    ) -> list[tuple[float, float, float]] | None:
        """Реализация алгоритма A* для поиска пути в 3D пространстве.

        Args:
            start: Начальная точка (x, y, z)
            goal: Целевая точка (x, y, z)
            obstacles: Список препятствий
            max_height: Максимальная высота

        Returns:
            Список точек пути или None
        """
        start_grid = self._world_to_grid(start)
        goal_grid = self._world_to_grid(goal)

        # Проверяем начальную и конечную точки
        if not self._is_cell_free(start_grid, obstacles, max_height):
            return None
        if not self._is_cell_free(goal_grid, obstacles, max_height):
            return None

        # Структуры данных для A*
        open_set: list[tuple[float, int, int, int]] = []  # (f_score, gx, gy, gz)
        came_from: dict[tuple[int, int, int], tuple[int, int, int] | None] = {}
        g_score: dict[tuple[int, int, int], float] = {start_grid: 0.0}
        f_score: dict[tuple[int, int, int], float] = {start_grid: self._heuristic(start_grid, goal_grid)}

        heappush(open_set, (f_score[start_grid], start_grid[0], start_grid[1], start_grid[2]))
        visited: set[tuple[int, int, int]] = set()

        while open_set:
            current_f, gx, gy, gz = heappop(open_set)
            current = (gx, gy, gz)

            if current in visited:
                continue

            visited.add(current)

            # Достигли цели
            if current == goal_grid:
                # Восстанавливаем путь
                path = []
                node: tuple[int, int, int] | None = current
                while node is not None:
                    path.append(self._grid_to_world(node))
                    node = came_from.get(node)
                path.reverse()
                return path

            # Проверяем соседей
            for dx, dy, dz in self.neighbors_26:
                neighbor = (current[0] + dx, current[1] + dy, current[2] + dz)

                if neighbor in visited:
                    continue

                if not self._is_cell_free(neighbor, obstacles, max_height):
                    continue

                # Вычисляем стоимость перехода
                # Диагональные перемещения стоят больше
                move_cost = math.sqrt(dx * dx + dy * dy + dz * dz) * self.grid_resolution
                # Штраф за вертикальное движение
                if dz != 0:
                    move_cost *= 1.2

                tentative_g_score = g_score.get(current, float("inf")) + move_cost

                if tentative_g_score < g_score.get(neighbor, float("inf")):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, goal_grid)
                    heappush(open_set, (f_score[neighbor], neighbor[0], neighbor[1], neighbor[2]))

        # Путь не найден
        return None

    def simplify_path(
        self, path: list[tuple[float, float, float]], obstacles: list[tuple[float, float, float]] | None = None
    ) -> list[tuple[float, float, float]]:
        """Упрощает путь, удаляя лишние точки.

        Args:
            path: Исходный путь
            obstacles: Список препятствий для проверки (опционально)

        Returns:
            Упрощенный путь
        """
        if len(path) <= 2:
            return path

        if obstacles is None:
            obstacles = []

        simplified = [path[0]]
        for i in range(1, len(path) - 1):
            # Проверяем, можно ли пропустить точку
            if not self._is_path_clear(simplified[-1], path[i + 1], obstacles):
                simplified.append(path[i])
        simplified.append(path[-1])

        return simplified
