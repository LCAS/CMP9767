"""Regression contracts for tutorial features retained after the Fortress migration."""

from pathlib import Path
import unittest

import yaml


REPOSITORY = Path(__file__).resolve().parents[3]
TUTORIAL = REPOSITORY / "src/cmp9767_tutorial"


class TestTutorialFollowupContract(unittest.TestCase):
    """Keep navigation and teaching nodes aligned with the Fortress interfaces."""

    def test_navigation_owns_installed_tutorial_assets_and_sim_time(self):
        source = (TUTORIAL / "launch/limo_navigation_bringup.launch.py").read_text(
            encoding="utf-8"
        )
        compact_source = "".join(source.split())
        setup = (TUTORIAL / "setup.py").read_text(encoding="utf-8")
        params = yaml.safe_load(
            (TUTORIAL / "param/nav2_params.yaml").read_text(encoding="utf-8")
        )

        self.assertIn('get_package_share_directory("cmp9767_tutorial")', source)
        self.assertIn('get_package_share_directory("nav2_bringup")', source)
        self.assertIn("RewrittenYaml", source)
        self.assertIn("configured_params", source)
        self.assertIn('"map",', source)
        self.assertIn('"frame_prefix",', source)
        self.assertIn('"scan_topic",', source)
        self.assertIn('"base_frame_id"', source)
        self.assertIn('"topic": scan_topic', source)
        self.assertNotIn("root_key=namespace", source)
        self.assertIn("'true' if '", source)
        self.assertIn(
            'DeclareLaunchArgument("use_sim_time",default_value="true"',
            compact_source,
        )
        self.assertIn("glob(path.join('maps', '*'))", setup)
        self.assertNotIn("glob(path.join('urdf', 'tidybot.*'))", setup)
        self.assertTrue(params["amcl"]["ros__parameters"]["use_sim_time"])
        self.assertTrue(params["planner_server"]["ros__parameters"]["use_sim_time"])
        self.assertNotIn("sit_map.yaml", str(params))

    def test_mapper_uses_simulation_time(self):
        mapper = yaml.safe_load(
            (TUTORIAL / "config/mapper_params_online_async.yaml").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(mapper["slam_toolbox"]["ros__parameters"]["use_sim_time"])

    def test_mapping_launch_owns_the_tutorial_slam_configuration(self):
        source = (TUTORIAL / "launch/limo_mapping_bringup.launch.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('get_package_share_directory("cmp9767_tutorial")', source)
        self.assertIn('package="slam_toolbox"', source)
        self.assertIn('"use_sim_time",', source)
        self.assertIn('"frame_prefix"', source)
        self.assertIn("PythonExpression", source)
        self.assertIn('"scan_topic"', source)

    def test_tutorial_nodes_can_select_a_robot_namespace_and_frame_prefix(self):
        helper = (TUTORIAL / "cmp9767_tutorial/simulation_interfaces.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("robot_namespace", helper)
        self.assertIn("frame_prefix", helper)
        for name in (
            "mover.py",
            "move_circle.py",
            "move_square.py",
            "detector_basic.py",
            "image_projection_1.py",
            "image_projection_2.py",
            "detector_3d.py",
            "counter_3d.py",
            "tf_listener.py",
            "demo_inspection.py",
        ):
            source = (TUTORIAL / "cmp9767_tutorial" / name).read_text(encoding="utf-8")
            self.assertIn("simulation_interfaces", source, name)

    def test_perception_uses_sensor_timestamps_for_tf(self):
        detector = (TUTORIAL / "cmp9767_tutorial/detector_3d.py").read_text(
            encoding="utf-8"
        )
        projection = (TUTORIAL / "cmp9767_tutorial/image_projection_2.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("ApproximateTimeSynchronizer", detector)
        self.assertIn("Time.from_msg", detector)
        self.assertIn("can_transform", detector)
        self.assertIn("Time.from_msg", projection)

    def test_watchdog_recovers_after_its_zero_velocity_command(self):
        watchdog = (
            REPOSITORY / "src/limo_gazebosim/scripts/twist_watchdog.py"
        ).read_text(encoding="utf-8")
        self.assertIn("is_zero_twist", watchdog)
        self.assertIn("self.timeout_triggered = False", watchdog)
        self.assertIn("if self.is_zero_twist(message):", watchdog)
        self.assertIn("f\"cmd_vel timed out after", watchdog)

    def test_demo_inspection_uses_the_selected_navigation_namespace(self):
        demo = (TUTORIAL / "cmp9767_tutorial/demo_inspection.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("rclpy.create_node", demo)
        self.assertIn("BasicNavigator(namespace=interfaces.robot_namespace)", demo)
        self.assertIn('declare_parameter("use_sim_time", True)', demo)

    def test_custom_world_uses_portable_sdf_and_model_metadata(self):
        world = (TUTORIAL / "worlds/custom_world.world").read_text(encoding="utf-8")
        self.assertNotIn("<ode>", world)
        self.assertNotIn("<bullet>", world)
        self.assertNotIn("<state ", world)
        self.assertNotIn("<laser_retro>", world)
        for config in TUTORIAL.glob("models/*/model.config"):
            self.assertIn('<sdf version="1.8">', config.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
