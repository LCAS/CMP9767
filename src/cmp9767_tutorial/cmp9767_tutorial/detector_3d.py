# Python libs
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy import qos

# OpenCV
import cv2

# ROS libraries
import image_geometry
from tf2_ros import Buffer, TransformListener
from tf2_geometry_msgs import do_transform_pose
from cv_bridge import CvBridge

# ROS Messages
from std_msgs.msg import Header
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import Pose, PoseStamped, Point, Quaternion

class Detector3D(Node):
    # use real robot?
    real_robot = False

    ccamera_model = None
    dcamera_model = None
    image_depth_ros = None

    min_area_size = 100
    global_frame = 'odom' # change to 'map' if using maps

    # aspect ratio between color and depth cameras
    # calculated as (color_horizontal_FOV/color_width) / (depth_horizontal_FOV/depth_width)
    color2depth_aspect = 1.0 # simulated camera
    camera_frame = 'depth_link' # for simulated robot

    if real_robot:
        color2depth_aspect = (71.0/640) / (67.9/400) # real camera
        camera_frame = 'camera_link' # for simulated robot

    visualisation = True

    def __init__(self):    
        super().__init__('Detector3D')
        self.bridge = CvBridge()

        # subscribers and publishers
        ccamera_info_topic = '/limo/depth_camera_link/camera_info'
        dcamera_info_topic = '/limo/depth_camera_link/depth/camera_info'
        cimage_topic = '/limo/depth_camera_link/image_raw'
        dimage_topic = '/limo/depth_camera_link/depth/image_raw'

        if self.real_robot:
            ccamera_info_topic = '/camera/color/camera_info'
            dcamera_info_topic = '/camera/depth/camera_info'
            cimage_topic = '/camera/color/image_raw'
            dimage_topic = '/camera/depth/image_raw'

        self.ccamera_info_sub = self.create_subscription(CameraInfo, ccamera_info_topic,
                                                self.ccamera_info_callback, qos_profile=qos.qos_profile_sensor_data)
        
        self.dcamera_info_sub = self.create_subscription(CameraInfo, dcamera_info_topic,
                                                self.dcamera_info_callback, qos_profile=qos.qos_profile_sensor_data)

        self.cimage_sub = self.create_subscription(Image, cimage_topic, 
                                                  self.image_color_callback, qos_profile=qos.qos_profile_sensor_data)
        
        self.dimage_sub = self.create_subscription(Image, dimage_topic, 
                                                  self.image_depth_callback, qos_profile=qos.qos_profile_sensor_data)
        
        self.object_location_pub = self.create_publisher(PoseStamped, '/object_location', qos.qos_profile_parameters)

        # tf functionality
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def image2camera_tf(self, image_coords, image_color, image_depth):
        # transform" from color to depth coordinates
        depth_coords = np.array(image_depth.shape[:2])/2 + (np.array(image_coords) - np.array(image_color.shape[:2])/2)*self.color2depth_aspect
        # get the depth reading at the centroid location
        depth_value = image_depth[int(depth_coords[0]), int(depth_coords[1])] # you might need to do some boundary checking first!
        # calculate object's 3d location in camera coords
        camera_coords = np.array(self.ccamera_model.projectPixelTo3dRay((image_coords[1], image_coords[0]))) #project the image coords (x,y) into 3D ray in camera coords 
        camera_coords /= camera_coords[2] # adjust the resulting vector so that z = 1
        camera_coords = camera_coords*depth_value # multiply the vector by depth
        pose = Pose(position=Point(x=camera_coords[0], y=camera_coords[1], z=camera_coords[2]), 
                    orientation=Quaternion(w=1.0))
        return pose
    
    def ccamera_info_callback(self, data):
        if self.ccamera_model is None:
            self.ccamera_model = image_geometry.PinholeCameraModel()
        self.ccamera_model.fromCameraInfo(data)

    def dcamera_info_callback(self, data):
        if self.dcamera_model is None:
            self.dcamera_model = image_geometry.PinholeCameraModel()
        self.dcamera_model.fromCameraInfo(data)

    def image_depth_callback(self, data):
        self.image_depth_ros = data

    def image_color_callback(self, data):
        # wait for camera models and depth image to arrive
        if self.ccamera_model is None or self.dcamera_model is None or self.image_depth_ros is None:
            return
        
        # covert image to open_cv
        self.image_color = self.bridge.imgmsg_to_cv2(data, "bgr8")
        self.image_depth = self.bridge.imgmsg_to_cv2(self.image_depth_ros, "32FC1")
        # real robot depth camera returns mm rather than m: normalise
        if self.real_robot:
            self.image_depth /= 1000.0

        # detect a color blob in the color image (here it is bright red)
        # provide the right values, or even better do it in HSV
        image_mask = cv2.inRange(self.image_color, (0, 0, 80), (50, 50, 255))

        # finding all separate image regions in the binary image, using connected components algorithm
        object_contours, _ = cv2.findContours( image_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # iterate through all detected objects/contours
        # calculate their image coordinates
        # and then project from image to global coordinates
        for num, cnt in enumerate(object_contours):
            area = cv2.contourArea(cnt)
            # detect only large objects
            if area > self.min_area_size:
                cmoms = cv2.moments(cnt)
                # calculate the y,x centroid
                image_coords = (cmoms["m01"] / cmoms["m00"], cmoms["m10"] / cmoms["m00"])
                # transform from image to camera coordinates
                camera_pose = self.image2camera_tf(image_coords, self.image_color, self.image_depth)

                # transform from the camera to global (odom or map) coordinates
                global_pose = do_transform_pose(camera_pose, 
                                                self.tf_buffer.lookup_transform(self.global_frame, self.camera_frame, rclpy.time.Time())) 

                # publish so we can see that in rviz
                self.object_location_pub.publish(PoseStamped(header=Header(frame_id=self.camera_frame),
                                              pose=global_pose))        

                print(f'--- object id {num} ---')
                print('image coords: ', image_coords)
                print('camera coords: ', camera_pose.position)
                print('global coords: ', global_pose.position)

                if self.visualisation:
                    # draw circles
                    cv2.circle(self.image_color, (int(image_coords[1]), int(image_coords[0])), 5, 255, -1)

        if self.visualisation:
            #resize and adjust for visualisation
            # image_color = cv2.resize(image_color, (0,0), fx=0.5, fy=0.5)
            self.image_depth *= 1.0/10.0 # scale for visualisation (max range 10.0 m)
            cv2.imshow("image color", self.image_color)
            cv2.imshow("image depth", self.image_depth)
            cv2.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    image_projection = Detector3D()
    rclpy.spin(image_projection)
    image_projection.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
