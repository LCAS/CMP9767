"""Print the fixed transform between the robot base and RGBD sensor."""

import rclpy
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener

from cmp9767_tutorial.simulation_interfaces import SimulationInterfaces


class TFListener(Node):
    """Report the current base-to-camera transform for the selected robot."""

    def __init__(self):
        super().__init__("tf_listener")
        self.interfaces = SimulationInterfaces.from_node(self)
        self.camera_frame = self.interfaces.frame("depth_link")
        self.base_frame = self.interfaces.frame("base_link")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def get_tf_transform(self):
        """Return the current base-to-camera transform when it is available."""
        try:
            return self.tf_buffer.lookup_transform(
                self.camera_frame, self.base_frame, rclpy.time.Time()
            )
        except TransformException as error:
            self.get_logger().warning(f"Failed to look up transform: {error}")
            return None


def main(args=None):
    """Print the transform until ROS shuts down."""
    rclpy.init(args=args)
    listener = TFListener()
    try:
        while rclpy.ok():
            transform = listener.get_tf_transform()
            if transform:
                translation = transform.transform.translation
                rotation = transform.transform.rotation
                listener.get_logger().info(
                    f"{transform.child_frame_id} relative to "
                    f"{transform.header.frame_id}: "
                    f"t=({translation.x:.3f}, {translation.y:.3f}, "
                    f"{translation.z:.3f}), "
                    f"q=({rotation.x:.3f}, {rotation.y:.3f}, "
                    f"{rotation.z:.3f}, {rotation.w:.3f})"
                )
            rclpy.spin_once(listener, timeout_sec=0.1)
    finally:
        listener.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
