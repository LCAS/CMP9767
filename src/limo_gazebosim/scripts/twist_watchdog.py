#!/usr/bin/env python3
"""Publish a zero velocity after command traffic stops."""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class TwistWatchdog(Node):
    """Send a single zero Twist when ``cmd_vel`` becomes stale."""

    def __init__(self):
        super().__init__('twist_watchdog')
        self.declare_parameter('timeout_sec', 0.5)
        self.timeout_sec = self.get_parameter('timeout_sec').value
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 1)
        self.subscription = self.create_subscription(
            Twist, 'cmd_vel', self.command_callback, 1)
        self.timer = self.create_timer(self.timeout_sec, self.timeout_callback)
        self.command_seen = False
        self.timeout_triggered = False

    def command_callback(self, _message):
        """Restart the watchdog after receiving a non-watchdog command."""
        if self.timeout_triggered:
            return
        self.command_seen = True
        self.timer.reset()

    def timeout_callback(self):
        """Stop the robot once after a command stream has gone quiet."""
        if self.command_seen and not self.timeout_triggered:
            self.get_logger().warning(
                'cmd_vel timed out after %.1f seconds; publishing zero Twist.',
                self.timeout_sec)
            self.timeout_triggered = True
            self.publisher.publish(Twist())


def main(args=None):
    """Run the Twist watchdog until ROS shuts down."""
    rclpy.init(args=args)
    watchdog = TwistWatchdog()
    try:
        rclpy.spin(watchdog)
    except KeyboardInterrupt:
        pass
    finally:
        watchdog.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
