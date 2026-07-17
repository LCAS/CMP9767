"""Detect red objects in RGBD data and publish their odometry-frame pose."""

import math

import cv2
import image_geometry
import message_filters
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import Point, Pose, PoseStamped, Quaternion
from rclpy import qos
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from sensor_msgs.msg import CameraInfo, Image
from tf2_geometry_msgs import do_transform_pose
from tf2_ros import Buffer, TransformListener

from cmp9767_tutorial.simulation_interfaces import SimulationInterfaces


class Detector3D(Node):
    """Project colour detections through synchronized RGBD observations."""

    min_area_size = 100
    visualisation = True

    def __init__(self):
        super().__init__("detector_3d")
        self.interfaces = SimulationInterfaces.from_node(self)
        self.declare_parameter("real_robot", False)
        self.declare_parameter("global_frame", self.interfaces.frame("odom"))
        self.real_robot = self.get_parameter("real_robot").value
        self.global_frame = self.get_parameter("global_frame").value
        self.bridge = CvBridge()
        self.ccamera_model = None
        self.dcamera_model = None
        self.color2depth_aspect = None

        cinfo_topic = self.interfaces.sensor_topic("depth_camera_link/camera_info")
        colour_topic = self.interfaces.sensor_topic("depth_camera_link/image_raw")
        depth_topic = self.interfaces.sensor_topic("depth_camera_link/depth/image_raw")
        self.camera_frame = self.interfaces.frame("depth_link")
        if self.real_robot:
            cinfo_topic = "/camera/color/camera_info"
            depth_info_topic = "/camera/depth/camera_info"
            colour_topic = "/camera/color/image_raw"
            depth_topic = "/camera/depth/image_raw"
            self.camera_frame = "camera_color_optical_frame"
        else:
            depth_info_topic = None

        self.create_subscription(
            CameraInfo,
            cinfo_topic,
            self.colour_camera_info_callback,
            qos_profile=qos.qos_profile_sensor_data,
        )
        if depth_info_topic:
            self.create_subscription(
                CameraInfo,
                depth_info_topic,
                self.depth_camera_info_callback,
                qos_profile=qos.qos_profile_sensor_data,
            )

        self.colour_sub = message_filters.Subscriber(
            self, Image, colour_topic, qos_profile=qos.qos_profile_sensor_data
        )
        self.depth_sub = message_filters.Subscriber(
            self, Image, depth_topic, qos_profile=qos.qos_profile_sensor_data
        )
        self.image_sync = message_filters.ApproximateTimeSynchronizer(
            [self.colour_sub, self.depth_sub], queue_size=10, slop=0.1
        )
        self.image_sync.registerCallback(self.image_callback)
        self.object_location_pub = self.create_publisher(
            PoseStamped,
            self.interfaces.topic("object_location"),
            qos.qos_profile_parameters,
        )
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def colour_camera_info_callback(self, data):
        """Store the colour camera model and aligned simulation depth model."""
        if self.ccamera_model is not None:
            return
        self.ccamera_model = image_geometry.PinholeCameraModel()
        self.ccamera_model.fromCameraInfo(data)
        if not self.real_robot:
            self.dcamera_model = self.ccamera_model
            self.color2depth_aspect = 1.0
        else:
            self.color2depth_calc()

    def depth_camera_info_callback(self, data):
        """Store the real robot's separate depth camera calibration."""
        if self.dcamera_model is not None:
            return
        self.dcamera_model = image_geometry.PinholeCameraModel()
        self.dcamera_model.fromCameraInfo(data)
        self.color2depth_calc()

    def color2depth_calc(self):
        """Calculate the relative image projection scale for real RGBD sensors."""
        if (
            self.color2depth_aspect is None
            and self.ccamera_model
            and self.dcamera_model
        ):
            colour_scale = math.atan2(
                self.ccamera_model.width, 2 * self.ccamera_model.fx()
            )
            depth_scale = math.atan2(
                self.dcamera_model.width, 2 * self.dcamera_model.fx()
            )
            self.color2depth_aspect = (
                colour_scale
                / self.ccamera_model.width
                / (depth_scale / self.dcamera_model.width)
            )

    def image2camera_pose(self, image_coords, colour_image, depth_image):
        """Project a colour-image centroid into the aligned depth camera frame."""
        depth_coords = (
            np.array(depth_image.shape[:2]) / 2
            + (np.array(image_coords) - np.array(colour_image.shape[:2]) / 2)
            * self.color2depth_aspect
        )
        row, column = depth_coords.astype(int)
        if (
            row < 0
            or column < 0
            or row >= depth_image.shape[0]
            or column >= depth_image.shape[1]
        ):
            return None
        depth_value = depth_image[row, column]
        if not np.isfinite(depth_value) or depth_value <= 0.0:
            return None
        camera_coords = np.array(
            self.ccamera_model.projectPixelTo3dRay((image_coords[1], image_coords[0]))
        )
        camera_coords /= camera_coords[2]
        camera_coords *= depth_value
        return Pose(
            position=Point(
                x=float(camera_coords[0]),
                y=float(camera_coords[1]),
                z=float(camera_coords[2]),
            ),
            orientation=Quaternion(w=1.0),
        )

    def image_callback(self, colour_data, depth_data):
        """Process a timestamp-aligned RGBD pair when its TF is available."""
        if self.color2depth_aspect is None:
            return
        stamp = Time.from_msg(colour_data.header.stamp)
        if not self.tf_buffer.can_transform(
            self.global_frame, self.camera_frame, stamp, timeout=Duration(seconds=0.1)
        ):
            self.get_logger().debug("Waiting for RGBD transform at sensor timestamp.")
            return
        try:
            transform = self.tf_buffer.lookup_transform(
                self.global_frame, self.camera_frame, stamp
            )
            colour_image = self.bridge.imgmsg_to_cv2(colour_data, "bgr8")
            depth_image = self.bridge.imgmsg_to_cv2(
                depth_data, "passthrough" if self.real_robot else "32FC1"
            )
        except Exception as error:  # CvBridge and TF errors are transient at startup.
            self.get_logger().warning(f"RGBD projection skipped: {error}")
            return
        if self.real_robot:
            depth_image = depth_image.astype(np.float32) / 1000.0

        image_mask = cv2.inRange(colour_image, (0, 0, 80), (50, 50, 255))
        object_contours, _ = cv2.findContours(
            image_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
        )
        for contour in object_contours:
            if cv2.contourArea(contour) <= self.min_area_size:
                continue
            moments = cv2.moments(contour)
            if moments["m00"] == 0.0:
                continue
            image_coords = (
                moments["m01"] / moments["m00"],
                moments["m10"] / moments["m00"],
            )
            camera_pose = self.image2camera_pose(
                image_coords, colour_image, depth_image
            )
            if camera_pose is None:
                continue
            global_pose = do_transform_pose(camera_pose, transform)
            message = PoseStamped()
            message.header.frame_id = self.global_frame
            message.header.stamp = colour_data.header.stamp
            message.pose = global_pose
            self.object_location_pub.publish(message)
            if self.visualisation:
                cv2.circle(
                    colour_image,
                    (int(image_coords[1]), int(image_coords[0])),
                    5,
                    255,
                    -1,
                )

        if self.visualisation:
            display_depth = cv2.resize(depth_image / 10.0, (0, 0), fx=0.5, fy=0.5)
            display_colour = cv2.resize(colour_image, (0, 0), fx=0.5, fy=0.5)
            cv2.imshow("image color", display_colour)
            cv2.imshow("image depth", display_depth)
            cv2.waitKey(1)


def main(args=None):
    """Run the detector until ROS shuts down."""
    rclpy.init(args=args)
    detector = Detector3D()
    try:
        rclpy.spin(detector)
    finally:
        detector.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
