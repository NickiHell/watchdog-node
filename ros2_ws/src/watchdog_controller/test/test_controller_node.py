"""Unit тесты для контроллера (mock тесты)."""

import pytest
from unittest.mock import Mock, patch
import rclpy
from watchdog_controller.controller_node import ControllerNode


class TestControllerNode:
    """Тесты для ControllerNode."""

    @pytest.fixture
    def node(self):
        """Создает экземпляр контроллера для тестов."""
        rclpy.init()
        node = ControllerNode()
        yield node
        node.destroy_node()
        rclpy.shutdown()

    def test_node_initialization(self, node):
        """Тест инициализации узла."""
        assert node.get_name() == 'controller_node'
        assert hasattr(node, 'cmd_vel_pub')
        assert hasattr(node, 'state_pub')
        assert hasattr(node, 'mode')

    def test_default_mode(self, node):
        """Тест режима по умолчанию."""
        # По умолчанию должен быть 'idle'
        assert node.mode == 'idle'

    def test_mode_parameter(self):
        """Тест установки режима через параметр."""
        rclpy.init()
        with patch('rclpy.node.Node.declare_parameter') as mock_declare, \
             patch('rclpy.node.Node.get_parameter') as mock_get:
            mock_get.return_value.get_parameter_value.return_value.string_value = 'navigation'
            node = ControllerNode()
            assert node.mode == 'navigation'
            node.destroy_node()
        rclpy.shutdown()

    def test_publishers_created(self, node):
        """Тест создания publishers."""
        assert node.cmd_vel_pub is not None
        assert node.state_pub is not None

    def test_timer_created(self, node):
        """Тест создания таймера."""
        # Проверяем что таймер существует (косвенно через update_loop)
        assert hasattr(node, 'update_loop')
        assert callable(node.update_loop)

