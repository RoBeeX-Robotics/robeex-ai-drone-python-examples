import cv2
from cv2.typing import MatLike
import numpy as np
from time import time
import math


# define names of each possible ArUco tag OpenCV supports
ARUCO_DICT = {
	"DICT_4X4_50": cv2.aruco.DICT_4X4_50,
	"DICT_4X4_100": cv2.aruco.DICT_4X4_100,
	"DICT_4X4_250": cv2.aruco.DICT_4X4_250,
	"DICT_4X4_1000": cv2.aruco.DICT_4X4_1000,
	"DICT_5X5_50": cv2.aruco.DICT_5X5_50,
	"DICT_5X5_100": cv2.aruco.DICT_5X5_100,
	"DICT_5X5_250": cv2.aruco.DICT_5X5_250,
	"DICT_5X5_1000": cv2.aruco.DICT_5X5_1000,
	"DICT_6X6_50": cv2.aruco.DICT_6X6_50,
	"DICT_6X6_100": cv2.aruco.DICT_6X6_100,
	"DICT_6X6_250": cv2.aruco.DICT_6X6_250,
	"DICT_6X6_1000": cv2.aruco.DICT_6X6_1000,
	"DICT_7X7_50": cv2.aruco.DICT_7X7_50,
	"DICT_7X7_100": cv2.aruco.DICT_7X7_100,
	"DICT_7X7_250": cv2.aruco.DICT_7X7_250,
	"DICT_7X7_1000": cv2.aruco.DICT_7X7_1000,
	"DICT_ARUCO_ORIGINAL": cv2.aruco.DICT_ARUCO_ORIGINAL,
	"DICT_APRILTAG_16h5": cv2.aruco.DICT_APRILTAG_16h5,
	"DICT_APRILTAG_25h9": cv2.aruco.DICT_APRILTAG_25h9,
	"DICT_APRILTAG_36h10": cv2.aruco.DICT_APRILTAG_36h10,
	"DICT_APRILTAG_36h11": cv2.aruco.DICT_APRILTAG_36h11
}

class AppArucoDetector:
    detector: cv2.aruco.ArucoDetector
    detector_params: cv2.aruco.DetectorParameters

    def __init__(self, calibration_path: str, tag_type: int = ARUCO_DICT["DICT_5X5_100"]) -> None:
        arucoDict = cv2.aruco.getPredefinedDictionary(tag_type)

        self.detector_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(arucoDict, self.detector_params)

        self.load_calibration(calibration_path)

        L = 0.1
        self.obj_points = np.array([
            [-L/2,  L/2, 0],  # top-left
            [ L/2,  L/2, 0],  # top-right
            [ L/2, -L/2, 0],  # bottom-right
            [-L/2, -L/2, 0]   # bottom-left
        ], dtype=np.float32)


        self.o = np.array([0.0,0.0,0.0])
        self.p = np.array([0.0,0.0,0.0])
        self.lt = time()

    def load_calibration(self, calibration_path: str):
        self.calib = np.load(calibration_path)
        self.mtx = self.calib['mtx']
        self.dist = self.calib['dist']
        self.rvecs = self.calib['rvecs']
        self.tvecs = self.calib['tvecs']
        print(self.mtx, self.dist)
        print(self.calib, self.calib.keys())
 
    def rotation_matrix_to_euler_angles(self, R):
        """
        Convert rotation matrix to Euler angles (roll, pitch, yaw)
        Roll  = rotation around X-axis
        Pitch = rotation around Y-axis
        Yaw   = rotation around Z-axis
        Returns angles in degrees.
        """
        sy = np.sqrt(R[0,0]**2 + R[1,0]**2)

        singular = sy < 1e-6

        if not singular:
            roll  = np.arctan2(R[2,1], R[2,2])
            pitch = np.arctan2(-R[2,0], sy)
            yaw   = np.arctan2(R[1,0], R[0,0])
        else:
            # Gimbal lock case
            roll  = np.arctan2(-R[1,2], R[1,1])
            pitch = np.arctan2(-R[2,0], sy)
            yaw   = 0

        # return np.degrees([roll, pitch, yaw])
        return [roll, pitch, yaw]

    def get_euler_angles(self, matrix):
        # This is a standard decomposition for a 3x3 rotation matrix
        sy = math.sqrt(matrix[0,0] * matrix[0,0] +  matrix[1,0] * matrix[1,0])
        singular = sy < 1e-6

        if not singular:
            x = math.atan2(matrix[2,1], matrix[2,2])
            y = math.atan2(-matrix[2,0], sy)
            z = math.atan2(matrix[1,0], matrix[0,0])
        else:
            x = math.atan2(-matrix[1,2], matrix[1,1])
            y = math.atan2(-matrix[2,0], sy)
            z = 0

        return np.rad2deg([x, y, z]) # Returns [Roll, Pitch, Yaw]


    def visualize_tag(self, tvec, rvec):
        """
        Visualize AR tag pose in 3D using PyVista.
        rvec: rotation vector from solvePnP
        tvec: translation vector from solvePnP
        L: tag side length (meters)
        """

        tvec = [tvec[2],-tvec[0],-tvec[1]]
        rvec = [rvec[2],-rvec[0], -rvec[1]]

        np_tvec = np.array(tvec)
        np_rvec = np.array(rvec)

        # cv2.show

        alpha = 0.2
        self.p = (self.p * (1 - alpha)) + ((alpha) * np_tvec)
        self.o = (self.o * (1 - alpha)) + ((alpha) * np_rvec)

        # actor.position = self.p
        # actor.orientation = self.o

    def detect_tag(self, f: MatLike):
        (tags_corners, ids, rejected) = self.detector.detectMarkers(f)


        # rvec = np.array([[0.1], [0.2], [0.3]])  # rotation vector
        # tvec = np.array([[0.0], [0.0], [0.5]])  # tag at 0.5 m in front of camera

        # print('april tags: ', len(tags_corners), 'rejected', len(rejected))
        # print('april tags: ', ids)
        # print('rejected april tags: ', rejected)

        # cv2.aruco.drawDetectedMarkers(f, rejected, None, (0, 0,255))

        if ids is None:
            return []

        ids = ids.flatten()
        cv2.aruco.drawDetectedMarkers(f, tags_corners, ids, (0, 255, 0))

        # Define the length of the axes
        axis_length = 0.1 
        
        # Define the 3D points in the object coordinate system
        axis_points = np.float32([
            [0, 0, 0],                # Origin
            [axis_length, 0, 0],      # X
            [0, axis_length, 0],      # Y
            [0, 0, axis_length]       # Z
        ])

        # print(rvecs)
        # Project 3D points to 2D image points
        img_pts, _ = cv2.projectPoints(axis_points, np.zeros((3, 1), dtype=np.float32), np.array([0,0,1.0], dtype=np.float32), self.mtx, self.dist)
        img_pts = img_pts.astype(int).reshape(-1, 2)

        # Draw the lines: (Origin to X, Origin to Y, Origin to Z)
        origin = tuple(img_pts[0])
        f = cv2.line(f, origin, tuple(img_pts[1]), (0, 0, 255), 3) # Red = X
        f = cv2.line(f, origin, tuple(img_pts[2]), (0, 255, 0), 3) # Green = Y
        f = cv2.line(f, origin, tuple(img_pts[3]), (255, 0, 0), 3) # Blue = Z

        tags = []
        for (markerCorner, markerID) in zip(tags_corners, ids):
            corners = markerCorner.reshape((4, 2)).astype(np.float32)

            # Solve PnP
            success, rvec, tvec = cv2.solvePnP(self.obj_points, corners, self.mtx, self.dist)
            # print(rvec, tvec)

            if success:
                # print('ef')

                # tvec = position of tag relative to camera (in meters)

                # Convert rotation vector to rotation matrix

                cv2.drawFrameAxes(f, self.mtx, self.dist, rvec, tvec, .1)
                x,y,z = tvec.ravel()
                R, _ = cv2.Rodrigues(rvec)
                rvec_simple = rvec.ravel()

                rot = self.rotation_matrix_to_euler_angles(R)
                # rot[0] += math.pi
                # if rot[0] > math.pi:
                #     rot[0] -= 2 * math.pi
                # # rot[0] %= 180
                # print(R)

                # print(f"Marker {markerID} position: x: {x:5.2f}, y: {y:5.2f}, z: {z:5.2f} --- r: {rot[0]:7.1f}, p: {rot[1]:7.2f}, y: {rot[2]:7.2f} --- ")
                # print(f"position: x: {self.o[0]:5.2f}, y: {self.o[1]:5.2f}, z: {self.o[2]:5.2f} --- r: {rot[0]:7.1f}, p: {rot[1]:7.2f}, y: {rot[2]:7.2f} --- ")

                # self.visualize_tag([x,y,z], rot)
                print(rvec_simple)
                tags.append({ 'id': int(markerID), 'pos': [float(x), float(y), float(z)], 'rot': list(map(float, rot)), 'R': list(map(list, R)), 'rvec': list(map(float, rvec_simple)) })

                # # Optional: draw axis for visualization
                # cv2.drawFrameAxes(f, mtx, dist, rvec, tvec, L*0.5)


        return tags
        # for _corners in tags_corners:
        #     corners = _corners[0]

        #     for p in corners:
        #         p = list(map(int, p))
        #         f = cv2.circle(f, p, 3, (0, 0, 255), -1)

