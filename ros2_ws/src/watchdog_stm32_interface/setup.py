from setuptools import setup
import os
from glob import glob

package_name = 'watchdog_stm32_interface'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools', 'pyserial'],
    zip_safe=True,
    maintainer='NickiHell',
    maintainer_email='nickihell@ya.ru',
    description='Interface package for communication with STM32 microcontroller',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'stm32_interface_node = watchdog_stm32_interface.stm32_interface_node:main',
        ],
    },
)

