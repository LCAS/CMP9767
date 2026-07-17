"""Start a self-contained Nav2 localization and navigation stack."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from nav2_common.launch import RewrittenYaml


def generate_launch_description():
    """Configure Nav2 from the tutorial's own map and parameter assets."""
    tutorial_share = get_package_share_directory("cmp9767_tutorial")
    nav2_share = get_package_share_directory("nav2_bringup")
    namespace = LaunchConfiguration("namespace")
    use_namespace = LaunchConfiguration("use_namespace")
    use_sim_time = LaunchConfiguration("use_sim_time")
    autostart = LaunchConfiguration("autostart")
    map_yaml_file = LaunchConfiguration("map")
    params_file = LaunchConfiguration("params_file")
    frame_prefix = LaunchConfiguration("frame_prefix")
    scan_topic = LaunchConfiguration("scan_topic")

    configured_params = RewrittenYaml(
        source_file=params_file,
        param_rewrites={
            "use_sim_time": use_sim_time,
            "base_frame_id": [frame_prefix, "base_footprint"],
            "odom_frame_id": [frame_prefix, "odom"],
            "global_frame_id": [frame_prefix, "map"],
            "frame_id": [frame_prefix, "map"],
            "robot_base_frame": [frame_prefix, "base_footprint"],
            "global_frame": [frame_prefix, "map"],
            "scan_topic": scan_topic,
            "topic": scan_topic,
        },
        convert_types=True,
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace", default_value="", description="Optional robot namespace."
            ),
            DeclareLaunchArgument(
                "use_namespace",
                default_value=PythonExpression(
                    ["'true' if '", namespace, "' else 'false'"]
                ),
                description=(
                    "Place Nav2 topics below namespace; inferred from a non-empty "
                    "namespace by default."
                ),
            ),
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Use the Fortress /clock bridge.",
            ),
            DeclareLaunchArgument(
                "frame_prefix",
                default_value=PythonExpression(
                    ["'", namespace, "/' if '", namespace, "' else ''"]
                ),
                description="TF frame prefix; inferred from namespace by default.",
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
                "autostart",
                default_value="true",
                description="Automatically activate Nav2.",
            ),
            DeclareLaunchArgument(
                "map",
                default_value=os.path.join(tutorial_share, "maps", "my_map.yaml"),
                description="Full path to the map YAML file.",
            ),
            DeclareLaunchArgument(
                "params_file",
                default_value=os.path.join(tutorial_share, "param", "nav2_params.yaml"),
                description="Full path to the Nav2 parameter file.",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(nav2_share, "launch", "bringup_launch.py")
                ),
                launch_arguments={
                    "namespace": namespace,
                    "use_namespace": use_namespace,
                    "slam": "false",
                    "map": map_yaml_file,
                    "use_sim_time": use_sim_time,
                    "params_file": configured_params,
                    "autostart": autostart,
                    "use_composition": "false",
                    "use_respawn": "false",
                }.items(),
            ),
        ]
    )
