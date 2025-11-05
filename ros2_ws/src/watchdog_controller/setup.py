from setuptools import setup
import os
from glob import glob

package_name = 'watchdog_controller'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    # Зависимость от watchdog_msgs будет добавлена после сборки
    # install_requires=['setuptools', 'watchdog_msgs'],
    zip_safe=True,
    maintainer='NickiHell',
    maintainer_email='nickihell@ya.ru',
    description='Main controller node for WatchDog robot',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'controller_node = watchdog_controller.controller_node:main',
        ],
    },
)

