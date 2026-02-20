from setuptools import find_packages, setup

package_name = "watchdog_detection"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="watchdog",
    maintainer_email="todo@todo.com",
    description="YOLOv8n + ByteTrack детекция и трекинг объектов",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "detection_node = watchdog_detection.detection_node:main",
        ],
    },
)
