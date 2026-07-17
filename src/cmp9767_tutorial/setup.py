from setuptools import find_packages, setup
from os import path
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
        (path.join('share', package_name, 'launch'), glob(path.join('launch', '*launch.[pxy][yma]*'))),
        (path.join('share', package_name, 'config'), glob(path.join('config', '*.yaml'))),
        (path.join('share', package_name, 'param'), glob(path.join('param', '*.yaml'))),
        (path.join('share', package_name, 'maps'), glob(path.join('maps', '*'))),
        (path.join('share', package_name, 'worlds'), glob(path.join('worlds', '*.world'))),
        (path.join('share', package_name, 'models', 'fire_extinguisher'), glob(path.join('models', 'fire_extinguisher', 'model.*'))),
        (path.join('share', package_name, 'models', 'first_aid_kit'), glob(path.join('models', 'first_aid_kit', 'model.*'))),
        (path.join('share', package_name, 'meshes'), glob(path.join('meshes', '*'))),
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
            'counter_3d = cmp9767_tutorial.counter_3d:main',
            'tf_listener = cmp9767_tutorial.tf_listener:main',            
            'demo_inspection = cmp9767_tutorial.demo_inspection:main'
        ],
    },
)
