"""Launch independently addressable LIMO robots on Gazebo Fortress."""

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
    existing = os.environ.get("IGN_GAZEBO_RESOURCE_PATH", "")
    os.environ["IGN_GAZEBO_RESOURCE_PATH"] = os.pathsep.join(
        filter(None, [existing, *paths])
    )


def generate_launch_description():
    urdf_model = LaunchConfiguration("urdf_model")
    world = LaunchConfiguration("world")
    use_sim_time = LaunchConfiguration("use_sim_time")
    use_simulator = LaunchConfiguration("use_simulator")
    use_robot_state_pub = LaunchConfiguration("use_robot_state_pub")
    use_rviz = LaunchConfiguration("use_rviz")
    gui = LaunchConfiguration("gui")
    headless = LaunchConfiguration("headless")
    rviz_config_file = LaunchConfiguration("rviz_config_file")

    description_share = get_package_share_directory("limo_description")
    simulation_share = get_package_share_directory("limo_gazebosim")
    tutorial_share = get_package_share_directory("cmp9767_tutorial")
    _append_resource_paths(
        [
            os.path.join(simulation_share, "models"),
            os.path.join(tutorial_share, "models"),
            description_share,
            simulation_share,
        ]
    )
    default_urdf = os.path.join(description_share, "urdf", "limo_four_diff.gazebo")
    default_world = os.path.join(simulation_share, "worlds", "simple.world")
    default_rviz = os.path.join(simulation_share, "rviz", "urdf.rviz")

    simulator = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                FindPackageShare("ros_gz_sim").find("ros_gz_sim"),
                "launch",
                "gz_sim.launch.py",
            )
        ),
        condition=IfCondition(use_simulator),
        launch_arguments={
            "gz_version": "6",
            "gz_args": [
                PythonExpression(
                    [
                        "'-r -s --headless-rendering ' if '",
                        headless,
                        "'.lower() == 'true' else '-r '",
                    ]
                ),
                world,
            ],
        }.items(),
    )
    actions = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("gui", default_value="false"),
        DeclareLaunchArgument("headless", default_value="false"),
        DeclareLaunchArgument("urdf_model", default_value=default_urdf),
        DeclareLaunchArgument("world", default_value=default_world),
        DeclareLaunchArgument("rviz_config_file", default_value=default_rviz),
        DeclareLaunchArgument("use_rviz", default_value="false"),
        DeclareLaunchArgument("use_robot_state_pub", default_value="true"),
        DeclareLaunchArgument("use_simulator", default_value="true"),
        simulator,
    ]
    delayed_actions = [
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            condition=IfCondition(use_simulator),
            arguments=["/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock"],
            output="screen",
        )
    ]

    for robot in (
        {"name": "limo1", "x": "0.0", "y": "0.0", "yaw": "0.0"},
        {"name": "limo2", "x": "2.0", "y": "0.0", "yaw": "0.0"},
    ):
        name = robot["name"]
        ns = name
        frame_prefix = f"{ns}/"
        standalone_without_gui = IfCondition(
            PythonExpression(
                [
                    "'",
                    use_simulator,
                    "'.lower() != 'true' and '",
                    gui,
                    "'.lower() != 'true'",
                ]
            )
        )
        standalone_with_gui = IfCondition(
            PythonExpression(
                [
                    "'",
                    use_simulator,
                    "'.lower() != 'true' and '",
                    gui,
                    "'.lower() == 'true'",
                ]
            )
        )
        actions.extend(
            [
                Node(
                    package="robot_state_publisher",
                    executable="robot_state_publisher",
                    namespace=ns,
                    condition=IfCondition(use_robot_state_pub),
                    parameters=[
                        {
                            "robot_description": Command(
                                [
                                    "xacro ",
                                    urdf_model,
                                    " model_name:=",
                                    name,
                                    " sensor_topic_prefix:=",
                                    ns,
                                    " frame_prefix:=",
                                    frame_prefix,
                                ]
                            ),
                            "use_sim_time": use_sim_time,
                            "frame_prefix": frame_prefix,
                        }
                    ],
                    remappings=[("/tf", "/tf"), ("/tf_static", "/tf_static")],
                    output="screen",
                ),
                Node(
                    package="joint_state_publisher",
                    executable="joint_state_publisher",
                    namespace=ns,
                    condition=standalone_without_gui,
                    parameters=[{"use_sim_time": use_sim_time}],
                    output="screen",
                ),
                Node(
                    package="joint_state_publisher_gui",
                    executable="joint_state_publisher_gui",
                    namespace=ns,
                    condition=standalone_with_gui,
                    parameters=[{"use_sim_time": use_sim_time}],
                    output="screen",
                ),
            ]
        )
        delayed_actions.extend(
            [
                Node(
                    package="ros_gz_sim",
                    executable="create",
                    condition=IfCondition(use_simulator),
                    arguments=[
                        "-name",
                        name,
                        "-topic",
                        f"/{ns}/robot_description",
                        "-x",
                        robot["x"],
                        "-y",
                        robot["y"],
                        "-z",
                        "0.0",
                        "-Y",
                        robot["yaw"],
                    ],
                    output="screen",
                ),
                Node(
                    package="ros_gz_bridge",
                    executable="parameter_bridge",
                    condition=IfCondition(use_simulator),
                    arguments=[
                        f"/model/{ns}/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist",
                        f"/model/{ns}/odometry@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
                        f"/model/{ns}/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model",
                        f"/{ns}/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
                        f"/{ns}/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU",
                        f"/model/{ns}/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
                        f"/{ns}/depth_camera/image@sensor_msgs/msg/Image[ignition.msgs.Image",
                        f"/{ns}/depth_camera/depth_image@sensor_msgs/msg/Image[ignition.msgs.Image",  # noqa: E501
                        f"/{ns}/depth_camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",  # noqa: E501
                    ],
                    remappings=[
                        (f"/model/{ns}/cmd_vel", f"/{ns}/cmd_vel"),
                        (f"/model/{ns}/odometry", f"/{ns}/odom"),
                        (f"/model/{ns}/joint_state", f"/{ns}/joint_states"),
                        (f"/{ns}/scan", f"/{ns}/scan"),
                        (f"/{ns}/imu", f"/{ns}/imu"),
                        (f"/model/{ns}/tf", "/tf"),
                        (
                            f"/{ns}/depth_camera/image",
                            f"/{ns}/depth_camera_link/image_raw",
                        ),
                        (
                            f"/{ns}/depth_camera/depth_image",
                            f"/{ns}/depth_camera_link/depth/image_raw",
                        ),
                        (
                            f"/{ns}/depth_camera/camera_info",
                            f"/{ns}/depth_camera_link/camera_info",
                        ),
                    ],
                    output="screen",
                ),
            ]
        )
    actions.extend(
        [
            TimerAction(period=3.0, actions=delayed_actions),
            Node(
                package="rviz2",
                executable="rviz2",
                condition=IfCondition(use_rviz),
                arguments=["-d", rviz_config_file],
                output="screen",
            ),
        ]
    )
    return LaunchDescription(actions)
