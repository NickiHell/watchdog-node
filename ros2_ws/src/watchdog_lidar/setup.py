from setuptools import setup
import os
from glob import glob

package_name = 'watchdog_lidar'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='NickiHell',
    maintainer_email='nickihell@ya.ru',
    description='LiDAR driver with support for multiple models',
    license='MIT',
    tests_require=['pytest', 'pytest-cov'],
    test_suite='test',
    entry_points={
        'console_scripts': [
            'lidar_node = watchdog_lidar.lidar_node:main',
        ],
    },
)

