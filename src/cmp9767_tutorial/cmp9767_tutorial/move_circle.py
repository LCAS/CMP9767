#!/usr/bin/env python

# An example of TurtleBot 3 drawing a 1 meter square.
# Written for humble

import rclpy
from geometry_msgs.msg import Twist
from math import radians
from rclpy.node import Node

from cmp9767_tutorial.simulation_interfaces import SimulationInterfaces


class MoveInACircle(Node):
    def __init__(self):
        super().__init__("move_circle")
        self.interfaces = SimulationInterfaces.from_node(self)
        self.cmd_vel_pub = self.create_publisher(
            Twist, self.interfaces.topic("cmd_vel"), 10
        )
        timer_period = 0.1  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        self.move_cmd = Twist()
        self.move_cmd.linear.x = 0.05  # m/s
        self.move_cmd.angular.z = radians(10)
        # 10 deg/s in radians/s

    def timer_callback(self):
        self.cmd_vel_pub.publish(self.move_cmd)


def main(args=None):
    rclpy.init(args=args)
    try:
        node = MoveInACircle()
        rclpy.spin(node)
        node.destroy_node()
        rclpy.shutdown()

    except Exception as e:
        print("node terminated. %s", e)


if __name__ == "__main__":
    main()
