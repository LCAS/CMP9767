from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'cmp9767_tutorial'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('launch/*launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Riccardo Polvara',
    maintainer_email='rpolvara@lincoln.ac.uk',
    description='Code for the CMP9767 module (Robot Programming) offered at the University of Lincoln, UK.',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mover = cmp9767_tutorial.mover:main',
            'move_square = cmp9767_tutorial.move_square:main',
            'move_circle = cmp9767_tutorial.move_circle:main',
            'image_projection_1 = cmp9767_tutorial.image_projection_1:main',
            'image_projection_2 = cmp9767_tutorial.image_projection_2:main',
            'detector_basic = cmp9767_tutorial.detector_basic:main',
            'detector_3d = cmp9767_tutorial.detector_3d:main',
            'tf_listener = cmp9767_tutorial.tf_listener:main',            
            'demo_inspection = cmp9767_tutorial.demo_inspection:main'
        ],
    },
)
