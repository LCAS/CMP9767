"""Launch the single LIMO DiffDrive simulation on Gazebo Fortress."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def _append_resource_paths(paths):
    """Add local simulator resources without discarding caller settings."""
    existing = os.environ.get('IGN_GAZEBO_RESOURCE_PATH', '')
    os.environ['IGN_GAZEBO_RESOURCE_PATH'] = os.pathsep.join(
        filter(None, [existing, *paths]))


def generate_launch_description():
    """Create the Fortress simulator, the robot, and its ROS interfaces."""
    use_sim_time = LaunchConfiguration('use_sim_time')
    gui = LaunchConfiguration('gui')
    headless = LaunchConfiguration('headless')
    namespace = LaunchConfiguration('namespace')
    use_namespace = LaunchConfiguration('use_namespace')
    rviz_config_file = LaunchConfiguration('rviz_config_file')
    urdf_model = LaunchConfiguration('urdf_model')
    use_robot_state_pub = LaunchConfiguration('use_robot_state_pub')
    use_rviz = LaunchConfiguration('use_rviz')
    use_simulator = LaunchConfiguration('use_simulator')
    run_scan_tf_probe = LaunchConfiguration('run_scan_tf_probe')
    use_twist_watchdog = LaunchConfiguration('use_twist_watchdog')
    world = LaunchConfiguration('world')
    spawn_x = LaunchConfiguration('spawn_x')
    spawn_y = LaunchConfiguration('spawn_y')
    spawn_z = LaunchConfiguration('spawn_z')
    spawn_yaw = LaunchConfiguration('spawn_yaw')

    ros_namespace = PythonExpression([
        "'", namespace, "' if '", use_namespace,
        "'.lower() == 'true' else ''",
    ])

    def ros_topic(name):
        return PythonExpression([
            "'/' + '", ros_namespace, "' + '/", name, "' if '",
            ros_namespace, "' else '/", name, "'",
        ])

    robot_name = 'limo_gazebosim'
    description_share = get_package_share_directory('limo_description')
    simulation_share = get_package_share_directory('limo_gazebosim')
    _append_resource_paths([
        os.path.join(simulation_share, 'models'), description_share, simulation_share,
    ])

    default_urdf = os.path.join(
        description_share, 'urdf', 'limo_four_diff.gazebo')
    default_world = os.path.join(simulation_share, 'worlds', 'simple.world')
    default_rviz = os.path.join(simulation_share, 'rviz', 'urdf.rviz')

    standalone_without_gui = IfCondition(PythonExpression([
        "'", use_simulator, "'.lower() != 'true' and '", gui,
        "'.lower() != 'true'",
    ]))
    standalone_with_gui = IfCondition(PythonExpression([
        "'", use_simulator, "'.lower() != 'true' and '", gui,
        "'.lower() == 'true'",
    ]))

    simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            FindPackageShare('ros_gz_sim').find('ros_gz_sim'),
            'launch', 'gz_sim.launch.py')),
        condition=IfCondition(use_simulator),
        launch_arguments={
            'gz_version': '6',
            'gz_args': [PythonExpression([
                "'-r -s --headless-rendering ' if '", headless,
                "'.lower() == 'true' else '-r '",
            ]), world],
        }.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        namespace=ros_namespace,
        condition=IfCondition(use_robot_state_pub),
        parameters=[{
            'robot_description': Command([
                'xacro ', urdf_model, ' model_name:=', robot_name,
                ' sensor_topic_prefix:=', robot_name, ' frame_prefix:=',
            ]),
            'use_sim_time': use_sim_time,
        }],
        output='screen',
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        condition=standalone_without_gui,
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )
    joint_state_publisher_gui = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        condition=standalone_with_gui,
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        condition=IfCondition(use_simulator),
        arguments=[
            '-name', robot_name, '-topic', ros_topic('robot_description'), '-x', spawn_x,
            '-y', spawn_y, '-z', spawn_z, '-Y', spawn_yaw,
        ],
        output='screen',
    )
    bridge_clock = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        condition=IfCondition(use_simulator),
        arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
        output='screen',
    )
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        condition=IfCondition(use_simulator),
        arguments=[
            f'/model/{robot_name}/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist',
            f'/model/{robot_name}/odometry@nav_msgs/msg/Odometry[ignition.msgs.Odometry',
            f'/model/{robot_name}/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model',
            f'/{robot_name}/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan',
            f'/{robot_name}/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU',
            f'/model/{robot_name}/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V',
            f'/{robot_name}/depth_camera/image@sensor_msgs/msg/Image[ignition.msgs.Image',
            f'/{robot_name}/depth_camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image',
            f'/{robot_name}/depth_camera/camera_info@sensor_msgs/msg/CameraInfo['
            'ignition.msgs.CameraInfo',
        ],
        remappings=[
            (f'/model/{robot_name}/cmd_vel', ros_topic('cmd_vel')),
            (f'/model/{robot_name}/odometry', ros_topic('odom')),
            (f'/model/{robot_name}/joint_state', ros_topic('joint_states')),
            (f'/{robot_name}/scan', ros_topic('scan')),
            (f'/{robot_name}/imu', ros_topic('imu')),
            (f'/model/{robot_name}/tf', '/tf'),
            (f'/{robot_name}/depth_camera/image',
             ros_topic('depth_camera_link/image_raw')),
            (f'/{robot_name}/depth_camera/depth_image',
             ros_topic('depth_camera_link/depth/image_raw')),
            (f'/{robot_name}/depth_camera/camera_info',
             ros_topic('depth_camera_link/camera_info')),
        ],
        output='screen',
    )
    scan_tf_probe = Node(
        package='limo_gazebosim',
        executable='scan_tf_probe.py',
        condition=IfCondition(run_scan_tf_probe),
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
    )
    twist_watchdog = Node(
        package='limo_gazebosim',
        executable='twist_watchdog.py',
        namespace=ros_namespace,
        condition=IfCondition(use_twist_watchdog),
        output='screen',
    )
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        condition=IfCondition(use_rviz),
        arguments=['-d', rviz_config_file],
        output='screen',
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('gui', default_value='false'),
        DeclareLaunchArgument('headless', default_value='false'),
        DeclareLaunchArgument('namespace', default_value=''),
        DeclareLaunchArgument('use_namespace', default_value='false'),
        DeclareLaunchArgument('urdf_model', default_value=default_urdf),
        DeclareLaunchArgument('world', default_value=default_world),
        DeclareLaunchArgument('rviz_config_file', default_value=default_rviz),
        DeclareLaunchArgument('use_robot_state_pub', default_value='true'),
        DeclareLaunchArgument('use_rviz', default_value='false'),
        DeclareLaunchArgument('use_simulator', default_value='true'),
        DeclareLaunchArgument('run_scan_tf_probe', default_value='false'),
        DeclareLaunchArgument('use_twist_watchdog', default_value='false'),
        DeclareLaunchArgument('spawn_x', default_value='2.0'),
        DeclareLaunchArgument('spawn_y', default_value='2.0'),
        DeclareLaunchArgument('spawn_z', default_value='1.0'),
        DeclareLaunchArgument('spawn_yaw', default_value='0.0'),
        simulator,
        robot_state_publisher,
        joint_state_publisher,
        joint_state_publisher_gui,
        twist_watchdog,
        TimerAction(period=3.0, actions=[
            spawn_robot,
            bridge_clock,
            bridge,
            scan_tf_probe,
        ]),
        rviz,
    ])
