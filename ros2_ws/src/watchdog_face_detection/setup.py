from setuptools import setup
import os
from glob import glob

package_name = 'watchdog_face_detection'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'scripts'), glob('scripts/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='NickiHell',
    maintainer_email='nickihell@ya.ru',
    description='Face detection and recognition with face database',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'face_detection_node = watchdog_face_detection.face_detection_node:main',
            'object_detection_node = watchdog_face_detection.object_detection_node:main',
            'add_face_to_db = watchdog_face_detection.add_face_to_db:main',
        ],
    },
)
