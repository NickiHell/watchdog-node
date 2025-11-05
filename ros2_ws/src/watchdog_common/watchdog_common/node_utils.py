"""Утилиты для упрощения работы с ROS2 узлами."""

from typing import Any, Optional, TypeVar, Callable
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy

T = TypeVar('T')


class BaseWatchdogNode(Node):
    """Базовый класс для всех узлов WatchDog с общими утилитами."""

    def __init__(self, node_name: str):
        """Инициализирует базовый узел.

        Args:
            node_name: Имя узла
        """
        super().__init__(node_name)
        self._param_cache: dict[str, Any] = {}

    def get_param(self, name: str, default: Any = None) -> Any:
        """Получает параметр с кэшированием.

        Args:
            name: Имя параметра
            default: Значение по умолчанию (если параметр не объявлен)

        Returns:
            Значение параметра
        """
        if name in self._param_cache:
            return self._param_cache[name]

        if not self.has_parameter(name):
            if default is not None:
                self.declare_parameter(name, default)
            else:
                raise ValueError(f'Параметр {name} не объявлен и не указано значение по умолчанию')

        param = self.get_parameter(name)
        value = self._get_param_value(param)
        self._param_cache[name] = value
        return value

    def get_param_str(self, name: str, default: Optional[str] = None) -> str:
        """Получает строковый параметр."""
        return str(self.get_param(name, default))

    def get_param_int(self, name: str, default: Optional[int] = None) -> int:
        """Получает целочисленный параметр."""
        return int(self.get_param(name, default))

    def get_param_float(self, name: str, default: Optional[float] = None) -> float:
        """Получает вещественный параметр."""
        return float(self.get_param(name, default))

    def get_param_bool(self, name: str, default: Optional[bool] = None) -> bool:
        """Получает булевый параметр."""
        return bool(self.get_param(name, default))

    def get_param_list(self, name: str, default: Optional[list] = None) -> list:
        """Получает список параметров."""
        value = self.get_param(name, default)
        return list(value) if value is not None else []

    def _get_param_value(self, param) -> Any:
        """Извлекает значение из параметра."""
        param_value = param.get_parameter_value()

        if param_value.type == 1:  # ParameterType.PARAMETER_BOOL
            return param_value.bool_value
        elif param_value.type == 2:  # ParameterType.PARAMETER_INTEGER
            return param_value.integer_value
        elif param_value.type == 3:  # ParameterType.PARAMETER_DOUBLE
            return param_value.double_value
        elif param_value.type == 4:  # ParameterType.PARAMETER_STRING
            return param_value.string_value
        elif param_value.type == 5:  # ParameterType.PARAMETER_BYTE_ARRAY
            return list(param_value.byte_array_value)
        elif param_value.type == 6:  # ParameterType.PARAMETER_BOOL_ARRAY
            return list(param_value.bool_array_value)
        elif param_value.type == 7:  # ParameterType.PARAMETER_INTEGER_ARRAY
            return list(param_value.integer_array_value)
        elif param_value.type == 8:  # ParameterType.PARAMETER_DOUBLE_ARRAY
            return list(param_value.double_array_value)
        elif param_value.type == 9:  # ParameterType.PARAMETER_STRING_ARRAY
            return list(param_value.string_array_value)
        else:
            return None

    def get_sensor_qos(self, depth: int = 10) -> QoSProfile:
        """Возвращает QoS профиль для сенсорных данных."""
        return QoSProfile(
            depth=depth,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )

    def get_control_qos(self, depth: int = 10) -> QoSProfile:
        """Возвращает QoS профиль для управляющих команд."""
        return QoSProfile(
            depth=depth,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.VOLATILE,
        )


def run_node(node_class: type[Node], args: Optional[list] = None) -> None:
    """Универсальная функция для запуска ROS2 узла.

    Args:
        node_class: Класс узла (должен быть наследником Node)
        args: Аргументы командной строки (опционально)

    Пример:
        run_node(ControllerNode)
    """
    import rclpy

    rclpy.init(args=args)
    node = node_class()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


def safe_get_param(node: Node, name: str, default: Any = None, param_type: type = str) -> Any:
    """Безопасно получает параметр узла с обработкой ошибок.

    Args:
        node: ROS2 узел
        name: Имя параметра
        default: Значение по умолчанию
        param_type: Тип параметра (str, int, float, bool)

    Returns:
        Значение параметра или значение по умолчанию
    """
    try:
        if not node.has_parameter(name) and default is not None:
            node.declare_parameter(name, default)

        param = node.get_parameter(name)
        param_value = param.get_parameter_value()

        if param_type == str:
            return param_value.string_value
        elif param_type == int:
            return param_value.integer_value
        elif param_type == float:
            return param_value.double_value
        elif param_type == bool:
            return param_value.bool_value
        else:
            return default

    except Exception as e:
        node.get_logger().warn(f'Ошибка получения параметра {name}: {e}, используется значение по умолчанию')
        return default

