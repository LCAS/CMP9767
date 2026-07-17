#!/usr/bin/env python3
"""Verify that each LaserScan timestamp has the required TF transforms."""

import sys

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.time import Time
from sensor_msgs.msg import Imu, LaserScan
from tf2_ros import Buffer, TransformException, TransformListener


class ScanTfProbe(Node):
    """Fail fast when sensor timestamps cannot be transformed into TF."""

    def __init__(self):
        super().__init__('scan_tf_probe')
        self.declare_parameter('required_samples', 30)
        self.declare_parameter('timeout_sec', 30.0)
        self.required_samples = self.get_parameter('required_samples').value
        self.valid_samples = 0
        self.invalid_samples = 0
        self.imu_valid = False
        self.valid_imu_samples = 0
        self.finished = False

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.create_subscription(
            LaserScan, '/scan', self.scan_callback, qos_profile_sensor_data)
        self.create_subscription(
            Imu, '/imu', self.imu_callback, qos_profile_sensor_data)
        self.timeout_timer = self.create_timer(
            self.get_parameter('timeout_sec').value, self.timeout_callback)

        self.get_logger().info(
            'Waiting for %d /scan messages with base_link -> laser_link and '
            'odom -> base_link available at the scan timestamp, plus an /imu '
            'message with base_link -> imu_link.' %
            self.required_samples)

    def scan_callback(self, scan):
        """Check both transform legs against the exact incoming scan time."""
        if self.finished:
            return

        if scan.header.frame_id != 'laser_link':
            self.record_failure(
                "Expected /scan frame_id 'laser_link', received '%s'." %
                scan.header.frame_id)
            return

        scan_time = Time.from_msg(scan.header.stamp)
        try:
            self.tf_buffer.lookup_transform(
                'base_link', 'laser_link', scan_time,
                timeout=Duration(seconds=0.2))
            self.tf_buffer.lookup_transform(
                'odom', 'base_link', scan_time,
                timeout=Duration(seconds=0.2))
        except TransformException as error:
            self.record_failure(
                'No transform for scan timestamp %d.%09d: %s' % (
                    scan.header.stamp.sec, scan.header.stamp.nanosec, error))
            return

        self.valid_samples += 1
        if self.valid_samples == 1 or self.valid_samples == self.required_samples:
            self.get_logger().info(
                'Validated scan timestamp %d.%09d (%d/%d).' % (
                    scan.header.stamp.sec, scan.header.stamp.nanosec,
                    self.valid_samples, self.required_samples))
        self.finish_if_ready()

    def imu_callback(self, imu):
        """Check the IMU header and its static transform at its message time."""
        if self.finished:
            return

        if imu.header.frame_id != 'imu_link':
            self.record_failure(
                "Expected /imu frame_id 'imu_link', received '%s'." %
                imu.header.frame_id)
            return

        imu_time = Time.from_msg(imu.header.stamp)
        try:
            self.tf_buffer.lookup_transform(
                'base_link', 'imu_link', imu_time,
                timeout=Duration(seconds=0.2))
        except TransformException as error:
            self.record_failure(
                'No transform for IMU timestamp %d.%09d: %s' % (
                    imu.header.stamp.sec, imu.header.stamp.nanosec, error))
            return

        self.imu_valid = True
        self.valid_imu_samples += 1
        if self.valid_imu_samples == 1:
            self.get_logger().info(
                'Validated IMU timestamp %d.%09d.' % (
                    imu.header.stamp.sec, imu.header.stamp.nanosec))
        self.finish_if_ready()

    def finish_if_ready(self):
        """Pass only after the scan and IMU contracts have both been observed."""
        if self.valid_samples >= self.required_samples and self.imu_valid:
            self.finish(0, 'LaserScan and IMU TF probe passed.')

    def record_failure(self, message):
        """Record an invalid scan without hiding an intermittent TF failure."""
        self.invalid_samples += 1
        self.get_logger().error(message)

    def timeout_callback(self):
        """Finish with a non-zero result if the requested sample set is absent."""
        self.finish(
            1,
            'Sensor TF probe timed out: %d valid scans, %d valid IMU messages, '
            '%d invalid samples.' % (
                self.valid_samples, self.valid_imu_samples, self.invalid_samples))

    def finish(self, exit_code, message):
        """Stop processing once the probe has a definitive result."""
        if self.finished:
            return
        self.finished = True
        log = self.get_logger().info if exit_code == 0 else self.get_logger().error
        log(message)
        self.timeout_timer.cancel()
        self.exit_code = exit_code


def main():
    rclpy.init()
    probe = ScanTfProbe()
    exit_code = 1
    try:
        while rclpy.ok() and not probe.finished:
            rclpy.spin_once(probe, timeout_sec=0.1)
        exit_code = probe.exit_code
    except KeyboardInterrupt:
        probe.get_logger().warning('LaserScan TF probe interrupted.')
    finally:
        probe.destroy_node()
        rclpy.shutdown()
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
