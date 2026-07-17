from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

from cmp9767_tutorial.simulation_interfaces import SimulationInterfaces


class Mover(Node):
    """
    A very simple Roamer implementation for LIMO.
    It simply goes straight until any obstacle is within
    2 m distance and then just simply turns left.
    A purely reactive approach.
    """

    def __init__(self):
        """
        On construction of the object, create a Subscriber
        to listen to lasr scans and a Publisher to control
        the robot
        """
        super().__init__("mover")
        self.interfaces = SimulationInterfaces.from_node(self)
        self.publisher = self.create_publisher(
            Twist, self.interfaces.topic("cmd_vel"), 10
        )
        self.subscriber = self.create_subscription(
            LaserScan, self.interfaces.topic("scan"), self.laserscan_callback, 10
        )

    def laserscan_callback(self, data):
        """
        Callback called any time a new laser scan become available
        """
        centre = len(data.ranges) // 2
        scan_window = data.ranges[centre - 10 : centre + 10]  # noqa: E203
        min_dist = min(scan_window)
        # print("Min: ", min_dist)
        t = Twist()
        if min_dist < 0.5:
            t.angular.z = 0.5
        else:
            t.linear.x = 0.8
        self.publisher.publish(t)


def main(args=None):
    rclpy.init(args=args)
    mover = Mover()
    rclpy.spin(mover)

    mover.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
