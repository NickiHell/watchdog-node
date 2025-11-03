from setuptools import setup
import os
from glob import glob

package_name = 'watchdog_speech'

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
    description='Speech recognition and synthesis with voice verification',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'speech_node = watchdog_speech.speech_node:main',
            'record_voice_sample = watchdog_speech.record_voice_sample:main',
        ],
    },
)

