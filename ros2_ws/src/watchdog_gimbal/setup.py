from setuptools import find_packages, setup

package_name = "watchdog_gimbal"

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
    description="Управление подвесом SIYI A8 mini (MAVLink Gimbal v2)",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "gimbal_node = watchdog_gimbal.gimbal_node:main",
        ],
    },
)
