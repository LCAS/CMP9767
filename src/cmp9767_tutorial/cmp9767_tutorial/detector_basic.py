import rclpy
from rclpy.node import Node
from rclpy import qos

import cv2 as cv

from sensor_msgs.msg import Image
from geometry_msgs.msg import Polygon, PolygonStamped, Point32
from cv_bridge import CvBridge

class DetectorBasic(Node):
    visualisation = True

    def __init__(self):    
        super().__init__('detector_basic')
        self.bridge = CvBridge()

        self.min_area_size = 100.0
        self.countour_color = (255, 255, 0) # cyan
        self.countour_width = 1 # in pixels

        self.object_pub = self.create_publisher(PolygonStamped, '/object_polygon', qos_profile=qos.qos_profile_parameters)
        self.image_sub = self.create_subscription(Image, '/limo/depth_camera_link/image_raw', 
                                                  self.image_color_callback, qos_profile=qos.qos_profile_sensor_data)
        
    def image_color_callback(self, data):
        bgr_image = self.bridge.imgmsg_to_cv2(data, "bgr8") # convert ROS Image message to OpenCV format

        # detect a color blob in the color image
        # provide the right range values for each BGR channel (set to red bright objects)
        bgr_thresh = cv.inRange(bgr_image, (0, 0, 80), (50, 50, 255))

        # finding all separate image regions in the binary image, using connected components algorithm
        bgr_contours, _ = cv.findContours( bgr_thresh,
            cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)

        detected_objects = []
        for contour in bgr_contours:
            area = cv.contourArea(contour)
            # detect only large objects
            if area > self.min_area_size:
                # get the bounding box of the region
                bbx, bby, bbw, bbh = cv.boundingRect(contour)
                # append the bounding box of the region into a list
                detected_objects.append(Polygon(points = [Point32(x=float(bbx), y=float(bby)), Point32(x=float(bbw), y=float(bbh))]))
                if self.visualisation:
                    cv.rectangle(bgr_image, (bbx, bby), (bbx+bbw, bby+bbh), self.countour_color,  self.countour_width)

        # publish individual objects from the list
        # the header information is taken from the Image message
        for polygon in detected_objects:
            self.object_pub.publish(PolygonStamped(polygon=polygon, header=data.header))

        # visualise the image processing results    
        if self.visualisation:
            cv.imshow("colour image", bgr_image)
            cv.imshow("detection mask", bgr_thresh)
            cv.waitKey(1)

def main(args=None):
    rclpy.init(args=args)
    detector_basic = DetectorBasic()
    
    rclpy.spin(detector_basic)
    
    detector_basic.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()