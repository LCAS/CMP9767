"""Regression checks for the Gazebo Fortress launch contract."""

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
LAUNCH_FILES = (
    REPOSITORY / "src/limo_gazebosim/launch/limo_gazebo_diff.launch.py",
    REPOSITORY / "src/cmp9767_tutorial/launch/limo_simulation.launch.py",
    REPOSITORY / "src/cmp9767_tutorial/launch/limo_simulation_multi.launch.py",
)


class TestFortressMigrationContract(unittest.TestCase):
    """Keep Fortress-only conventions from regressing to Classic or gz-sim."""

    def test_launches_use_fortress_transport_and_resource_conventions(self):
        for launch_file in LAUNCH_FILES:
            source = launch_file.read_text(encoding="utf-8")
            self.assertIn("ignition.msgs.", source, launch_file)
            self.assertIn("IGN_GAZEBO_RESOURCE_PATH", source, launch_file)
            self.assertNotIn("gz.msgs.", source, launch_file)
            self.assertNotIn("GZ_SIM_RESOURCE_PATH", source, launch_file)

    def test_every_launch_bridges_clock_and_conditions_simulator_actions(self):
        for launch_file in LAUNCH_FILES:
            source = launch_file.read_text(encoding="utf-8")
            self.assertIn("/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock", source)
            self.assertGreaterEqual(
                source.count("condition=IfCondition(use_simulator)"), 3, launch_file
            )

    def test_headless_launches_enable_fortress_headless_rendering(self):
        """Headless camera and GPU lidar need the Fortress render server."""
        for launch_file in LAUNCH_FILES:
            source = launch_file.read_text(encoding="utf-8")
            self.assertIn("-r -s --headless-rendering", source, launch_file)

    def test_multi_robot_launch_keeps_sensor_topics_namespaced(self):
        source = LAUNCH_FILES[2].read_text(encoding="utf-8")
        self.assertIn('/{ns}/scan', source)
        self.assertIn('/{ns}/imu', source)
        self.assertIn('/{ns}/depth_camera/image', source)
        self.assertIn('/{ns}/depth_camera_link/image_raw', source)
        self.assertNotIn('/limo/depth_camera_link/image_raw', source)
        self.assertNotIn('"/cmd_vel"', source)

    def test_all_simulation_launches_use_native_joint_states(self):
        """Gazebo is the sole dynamic-joint authority while it is running."""
        for launch_file in LAUNCH_FILES:
            source = launch_file.read_text(encoding="utf-8")
            self.assertIn(
                "sensor_msgs/msg/JointState[ignition.msgs.Model", source, launch_file
            )
            self.assertIn("'.lower() != 'true'", source, launch_file)

    def test_models_use_fortress_sensor_syntax_and_parameterized_frames(self):
        for name in (
            "limo_four_diff.gazebo",
            "limo_ackerman.gazebo",
            "limo_gazebo.gazebo",
        ):
            source = (REPOSITORY / "src/limo_description/urdf" / name).read_text(
                encoding="utf-8"
            )
            self.assertNotIn("<ray>", source, name)
            self.assertNotIn('type="depth"', source, name)
            self.assertNotIn("libgazebo_ros_", source, name)
        robot = (
            REPOSITORY / "src/limo_description/urdf/limo_four_diff.gazebo"
        ).read_text(encoding="utf-8")
        shared = (
            REPOSITORY / "src/limo_description/urdf/limo_gazebo.gazebo"
        ).read_text(encoding="utf-8")
        self.assertIn("<lidar>", shared)
        self.assertIn("<gz_frame_id>${frame_prefix}laser_link</gz_frame_id>", shared)
        self.assertIn("<gz_frame_id>${frame_prefix}depth_link</gz_frame_id>", shared)
        self.assertIn("model_name", robot)
        self.assertIn("frame_prefix", robot)

    def test_multi_robot_launch_prefixes_all_tf_frames(self):
        source = LAUNCH_FILES[2].read_text(encoding="utf-8")
        self.assertIn(' frame_prefix:=', source)
        self.assertIn('"frame_prefix":', source)
        self.assertIn('f"{ns}/"', source)

    def test_multi_robot_launch_starts_two_independent_robots(self):
        source = LAUNCH_FILES[2].read_text(encoding="utf-8")
        self.assertIn('"name": "limo1"', source)
        self.assertIn('"name": "limo2"', source)
        self.assertIn('DeclareLaunchArgument("use_robot_state_pub"', source)
        self.assertIn("condition=IfCondition(use_robot_state_pub)", source)

    def test_simulation_package_does_not_install_python_bytecode(self):
        cmake = (REPOSITORY / "src/limo_gazebosim/CMakeLists.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn('PATTERN "__pycache__" EXCLUDE', cmake)

    def test_primary_launch_has_a_single_tf_authority_during_simulation(self):
        """Joint-state publishers are for standalone model display only."""
        source = LAUNCH_FILES[0].read_text(encoding="utf-8")
        self.assertIn("standalone_without_gui", source)
        self.assertIn("'.lower() != 'true'", source)
        self.assertIn("TimerAction", source)

    def test_simulation_package_installs_the_scan_tf_probe(self):
        probe = REPOSITORY / "src/limo_gazebosim/scripts/scan_tf_probe.py"
        self.assertTrue(probe.is_file())
        source = probe.read_text(encoding="utf-8")
        self.assertIn("'/scan'", source)
        self.assertIn("'base_link'", source)
        self.assertIn("'laser_link'", source)
        self.assertIn("'/imu'", source)
        self.assertIn("'imu_link'", source)
        self.assertIn("'odom'", source)
        primary_launch = LAUNCH_FILES[0].read_text(encoding="utf-8")
        self.assertIn("run_scan_tf_probe", primary_launch)

    def test_shipped_sdf_assets_use_the_fortress_sdf_version(self):
        """Avoid a mixed SDF dialect across worlds and included models."""
        asset_files = (
            *REPOSITORY.glob("src/limo_gazebosim/worlds/*.world"),
            *REPOSITORY.glob("src/limo_gazebosim/models/**/model.sdf"),
            *REPOSITORY.glob("src/cmp9767_tutorial/worlds/*.world"),
            *REPOSITORY.glob("src/cmp9767_tutorial/models/**/model.sdf"),
        )
        for asset_file in asset_files:
            source = asset_file.read_text(encoding="utf-8")
            self.assertRegex(source, r"<sdf version=['\"]1\.8['\"]>", asset_file)

    def test_shipped_sdf_assets_do_not_keep_classic_physics_extensions(self):
        """Fortress assets must not depend on ODE or Bullet-specific contact XML."""
        asset_files = (
            *REPOSITORY.glob("src/limo_gazebosim/worlds/*.world"),
            *REPOSITORY.glob("src/limo_gazebosim/models/**/model.sdf"),
            *REPOSITORY.glob("src/cmp9767_tutorial/worlds/*.world"),
            *REPOSITORY.glob("src/cmp9767_tutorial/models/**/model.sdf"),
        )
        for asset_file in asset_files:
            source = asset_file.read_text(encoding="utf-8")
            self.assertNotIn("<ode>", source, asset_file)
            self.assertNotIn("<bullet>", source, asset_file)
            self.assertNotIn("<laser_retro>", source, asset_file)

    def test_sensor_topics_are_explicit_and_worlds_load_the_imu_system(self):
        """Fortress publishes exactly the sensor topics configured in SDF."""
        robot = (
            REPOSITORY / "src/limo_description/urdf/limo_four_diff.gazebo"
        ).read_text(encoding="utf-8")
        shared = (
            REPOSITORY / "src/limo_description/urdf/limo_gazebo.gazebo"
        ).read_text(encoding="utf-8")
        self.assertIn("sensor_topic_prefix", robot)
        self.assertIn("/${sensor_topic_prefix}/scan", shared)
        self.assertIn("/${sensor_topic_prefix}/imu", shared)
        self.assertIn("/${sensor_topic_prefix}/depth_camera", shared)
        self.assertIn('type="rgbd_camera"', shared)
        self.assertIn("/${sensor_topic_prefix}/depth_camera/camera_info", shared)
        self.assertIn("<gz_frame_id>${frame_prefix}laser_link</gz_frame_id>", shared)
        self.assertNotIn("<frame_id>laser_link</frame_id>", shared)
        self.assertIn("ignition-gazebo-joint-state-publisher-system", robot)
        self.assertIn("/model/${model_name}/joint_state", robot)
        primary_launch = LAUNCH_FILES[0].read_text(encoding="utf-8")
        self.assertIn("sensor_msgs/msg/JointState[ignition.msgs.Model", primary_launch)
        self.assertIn("ros_topic('joint_states')", primary_launch)
        for world_file in REPOSITORY.glob("src/limo_gazebosim/worlds/*.world"):
            source = world_file.read_text(encoding="utf-8")
            self.assertIn("ignition-gazebo-imu-system", source, world_file)


if __name__ == "__main__":
    unittest.main()
