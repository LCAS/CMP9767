"""Resolve the tutorial's single- and multi-robot ROS interfaces."""

from dataclasses import dataclass


def _topic(namespace, suffix):
    """Return an absolute topic below an optional robot namespace."""
    suffix = suffix.lstrip("/")
    return f"/{namespace}/{suffix}" if namespace else f"/{suffix}"


@dataclass(frozen=True)
class SimulationInterfaces:
    """Topic and frame naming shared by the tutorial executable nodes."""

    robot_namespace: str
    frame_prefix: str

    @classmethod
    def from_node(cls, node):
        """Read optional namespace and frame-prefix parameters from ``node``."""
        node.declare_parameter("robot_namespace", "")
        node.declare_parameter("frame_prefix", "")
        namespace = node.get_parameter("robot_namespace").value.strip("/")
        frame_prefix = node.get_parameter("frame_prefix").value.strip("/")
        if not frame_prefix and namespace:
            frame_prefix = namespace
        return cls(namespace, f"{frame_prefix}/" if frame_prefix else "")

    def topic(self, suffix):
        """Return a robot-scoped tutorial topic."""
        return _topic(self.robot_namespace, suffix)

    def sensor_topic(self, suffix):
        """Return the RGBD sensor topic for this robot.

        The historical single-robot bridge uses ``/limo`` while the
        multi-robot bridge uses each robot name as the sensor namespace.
        """
        return _topic(self.robot_namespace or "limo", suffix)

    def frame(self, frame_id):
        """Return a unique TF frame ID for the selected robot."""
        return f"{self.frame_prefix}{frame_id}"
