from setuptools import setup

package_name = "watchdog_pixhawk_interface"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="NickiHell",
    maintainer_email="nickihell@example.com",
    description="Interface with Pixhawk flight controller via mavros",
    license="MIT",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "pixhawk_interface_node = watchdog_pixhawk_interface.pixhawk_interface_node:main",
            "rc_interface_node = watchdog_pixhawk_interface.rc_interface:main",
        ],
    },
)
