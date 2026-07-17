"""Start SLAM Toolbox against the Fortress single- or multi-robot bridge."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    """Create a mapping launch description with explicit simulation defaults."""
    package_share = get_package_share_directory("cmp9767_tutorial")
    namespace = LaunchConfiguration("namespace")
    frame_prefix = LaunchConfiguration("frame_prefix")
    use_sim_time = LaunchConfiguration("use_sim_time")
    params_file = LaunchConfiguration("params_file")
    scan_topic = LaunchConfiguration("scan_topic")

    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites={
            "use_sim_time": use_sim_time,
            "odom_frame": [frame_prefix, "odom"],
            "map_frame": [frame_prefix, "map"],
            "base_frame": [frame_prefix, "base_footprint"],
            "scan_topic": scan_topic,
        },
        convert_types=True,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="",
                description="Robot namespace for SLAM topics.",
            ),
            DeclareLaunchArgument(
                "frame_prefix",
                default_value=PythonExpression(
                    ["'", namespace, "/' if '", namespace, "' else ''"]
                ),
                description="TF frame prefix; inferred from namespace by default.",
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use the Fortress /clock bridge.",
            ),
            DeclareLaunchArgument(
                "scan_topic",
                default_value=PythonExpression(
                    [
                        "'/' + '",
                        namespace,
                        "' + '/scan' if '",
                        namespace,
                        "' else '/scan'",
                    ]
                ),
                description="LaserScan topic; inferred from namespace by default.",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(
                    package_share, "config", "mapper_params_online_async.yaml"
                ),
                description="SLAM Toolbox parameter file.",
            ),
            Node(
                package="slam_toolbox",
                executable="async_slam_toolbox_node",
                name="slam_toolbox",
                namespace=namespace,
                output="screen",
                parameters=[configured_params],
            ),
        ]
    )
