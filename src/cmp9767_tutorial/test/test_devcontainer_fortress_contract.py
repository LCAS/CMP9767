"""Regression checks for the Humble + Gazebo Fortress container contract."""

from pathlib import Path
import unittest


REPOSITORY = Path(__file__).resolve().parents[3]
DOCKERFILE = REPOSITORY / ".devcontainer/Dockerfile"
POST_CREATE = REPOSITORY / ".devcontainer/post-create.sh"
DEVCONTAINER = REPOSITORY / ".devcontainer/devcontainer.json"
RUNTIME_CHECK = REPOSITORY / ".devcontainer/validate_fortress_runtime.sh"
PACKAGE_XML = REPOSITORY / "src/cmp9767_tutorial/package.xml"


class TestDevcontainerFortressContract(unittest.TestCase):
    """Keep the development image pinned to the Fortress ROS integration."""

    def test_runtime_check_validates_fortress_and_ros_bridge(self):
        source = RUNTIME_CHECK.read_text(encoding="utf-8")
        self.assertIn("ign gazebo --version", source)
        self.assertIn("Gazebo[^0-9]*6", source)
        self.assertIn("ros_gz_sim", source)
        self.assertIn("ros_gz_bridge", source)
        self.assertIn("libignition-gazebo6-diff-drive-system.so", source)
        self.assertIn("libignition-gazebo6-sensors-system.so", source)

    def test_image_and_post_create_run_the_runtime_check(self):
        self.assertIn(
            "validate_fortress_runtime.sh", DOCKERFILE.read_text(encoding="utf-8")
        )
        self.assertIn(
            "validate_fortress_runtime.sh", POST_CREATE.read_text(encoding="utf-8")
        )

    def test_manifest_declares_direct_simulation_dependencies(self):
        source = PACKAGE_XML.read_text(encoding="utf-8")
        for dependency in (
            "ament_index_python",
            "launch",
            "launch_ros",
            "ros_gz_sim",
            "ros_gz_bridge",
            "robot_state_publisher",
            "joint_state_publisher",
            "xacro",
            "nav_msgs",
            "tf2_msgs",
            "rosgraph_msgs",
        ):
            self.assertIn(f"<exec_depend>{dependency}</exec_depend>", source)

    def test_image_does_not_install_the_broad_ros_gz_metapackage(self):
        source = DOCKERFILE.read_text(encoding="utf-8")
        self.assertNotIn("ros-${ROS_DISTRO}-ros-gz &&", source)
        self.assertNotIn("ros-${ROS_DISTRO}-ros-gz-sim", source)
        self.assertNotIn("ros-${ROS_DISTRO}-ros-gz-bridge", source)

    def test_devcontainer_uses_the_base_middleware_and_base_image_pin(self):
        """The migration must not override an otherwise working base contract."""
        source = DEVCONTAINER.read_text(encoding="utf-8")
        self.assertNotIn("RMW_IMPLEMENTATION", source)
        self.assertIn(
            "ARG BASE_IMAGE=lcas.lincoln.ac.uk/lcas/limo_platform:2.2",
            DOCKERFILE.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
