"""Launch файл для запуска веб-интерфейса."""

from launch import LaunchDescription
from launch.actions import ExecuteProcess
import os


def generate_launch_description():
    """Генерация launch описания."""

    # Путь к web_interface относительно корня проекта
    launch_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(launch_dir, "..", "..")
    web_dir = os.path.join(project_root, "web_interface")

    return LaunchDescription(
        [
            ExecuteProcess(
                cmd=["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
                cwd=web_dir,
                output="screen",
            ),
        ]
    )
