from cv2.typing import MatLike
import argparse
import cv2
import sys
import numpy as np
import pyvista as pv
from time import time

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cam", type=str,
        default="robeex",
        help="Camera")
    ap.add_argument("-t", "--type", type=str,
        default="DICT_5X5_100",
        help="type of ArUCo tag to generate")

    return vars(ap.parse_args())

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

L = 0.1

obj_points = np.array([
    [-L/2,  L/2, 0],  # top-left
    [ L/2,  L/2, 0],  # top-right
    [ L/2, -L/2, 0],  # bottom-right
    [-L/2, -L/2, 0]   # bottom-left
], dtype=np.float32)

args = parse_args()


is_using_robeex_cam = False
if args["cam"] == "robeex":
    is_using_robeex_cam = True

calib = np.load('calibration_data_robeex.npz' if is_using_robeex_cam else 'calibration_data_pc.npz')
mtx = calib['mtx']
dist = calib['dist']
rvecs = calib['rvecs']
tvecs = calib['tvecs']
print(mtx, dist)
print(calib, calib.keys())



plotter = pv.Plotter()
actors = {}

def make_tag_mesh(L=0.1):
    """Create a square plane mesh (tag)."""
    half = L / 2
    corners = np.array([
        [-half, -half, 0],
        [ half, -half, 0],
        [ half,  half, 0],
        [-half,  half, 0]
    ])
    faces = np.hstack([[4, 0, 1, 2, 3]])
    return pv.PolyData(corners, faces)

tag_size = 0.1  # meters


center_cube = pv.Cube(center=(0,0,0), x_length=0.1, y_length=0.1, z_length=0.1)
plotter.add_mesh(center_cube, color="white", opacity=0.8)

_arrow = pv.Arrow(start=(0,0.0,0), direction=(1,0,0))

cube = pv.Cube(center=(0,0.0,0), x_length=0.1, y_length=0.1, z_length=0.1)
colors = np.array([
    [1, 0, 0],   # red
    [0, 1, 0],   # green
    [0, 0, 1],   # blue
    [1, 1, 0],   # yellow
    [1, 0, 1],   # magenta
    [0, 1, 1]    # cyan
], dtype=np.float32)

# Assign colors to faces (cells)
cube.cell_data["colors"] = colors
actor = plotter.add_mesh(cube, scalars="colors", rgb=True, show_edges=True)
arrow = plotter.add_mesh(_arrow, show_edges=True, name="arrow")

plotter.add_axes(interactive=True)
# plotter.add_measurement_widget()
plotter.show(interactive_update=True)
# plotter.camera.

class AppArucoDetector:
    detector: cv2.aruco.ArucoDetector
    detector_params: cv2.aruco.DetectorParameters

    def __init__(self, tag_type: int = ARUCO_DICT["DICT_5X5_100"]) -> None:
        arucoDict = cv2.aruco.getPredefinedDictionary(tag_type)

        self.detector_params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(arucoDict, self.detector_params)
        a = cv2.aruco.RefineParameters()
        print(a.minRepDistance, a.errorCorrectionRate, a.checkAllOrders)
        self.o = np.array([0.0,0.0,0.0])
        self.p = np.array([0.0,0.0,0.0])
        self.lt = time()

 
    def rotationMatrixToEulerAngles(self, R):
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

        return np.degrees([roll, pitch, yaw])

    def get_euler_angles(matrix):
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

        actor.position = self.p
        actor.orientation = self.o

        s = np.linalg.norm(self.p)
        print(s)
        new_arrow = pv.Arrow(direction=self.p, scale='auto')
        plotter.add_mesh(new_arrow, name="arrow", color="magenta")

        # o2 = (self.p / np.linalg.norm(self.p)) * 360
        # o2 = [o2[0], o2[2], o2[1]]
        # arrow.orientation = o2
        # arrow.translate((0.5, 0, 0), inplace=True)
        
        # print(tvec, rvec)

        plotter.update()


    def detect_tag(self, f: MatLike):
        (tags_corners, ids, rejected) = self.detector.detectMarkers(f)


        # rvec = np.array([[0.1], [0.2], [0.3]])  # rotation vector
        # tvec = np.array([[0.0], [0.0], [0.5]])  # tag at 0.5 m in front of camera

        # print('april tags: ', len(tags_corners), 'rejected', len(rejected))
        # print('april tags: ', len(tags_corners))

        # cv2.aruco.drawDetectedMarkers(f, rejected, None, (0, 0,255))

        if ids is None:
            plotter.update()
            return []

        ids = ids.flatten()
        cv2.aruco.drawDetectedMarkers(f, tags_corners, ids, (0, 255, 0))

        tags = []
        for (markerCorner, markerID) in zip(tags_corners, ids):
            corners = markerCorner.reshape((4, 2)).astype(np.float32)

            # Solve PnP
            success, rvec, tvec = cv2.solvePnP(obj_points, corners, mtx, dist)
            # print(rvec, tvec)

            if success:
                # print('ef')

                # tvec = position of tag relative to camera (in meters)

                # Convert rotation vector to rotation matrix
                x,y,z = tvec.ravel()
                R, _ = cv2.Rodrigues(rvec)

                rot = self.rotationMatrixToEulerAngles(R)
                rot[0] += 180  
                if rot[0] > 180:
                    rot[0] -= 360
                # rot[0] %= 180

                print(f"Marker {markerID} position: x: {x:5.2f}, y: {y:5.2f}, z: {z:5.2f} --- r: {rot[0]:7.1f}, p: {rot[1]:7.2f}, y: {rot[2]:7.2f} --- ")
                # print(f"position: x: {self.o[0]:5.2f}, y: {self.o[1]:5.2f}, z: {self.o[2]:5.2f} --- r: {rot[0]:7.1f}, p: {rot[1]:7.2f}, y: {rot[2]:7.2f} --- ")

                self.visualize_tag([x,y,z], rot)
                tags.append({ 'pos': [x, y, z], 'rot': rot })

                # # Optional: draw axis for visualization
                # cv2.drawFrameAxes(f, mtx, dist, rvec, tvec, L*0.5)


        return tags
        # for _corners in tags_corners:
        #     corners = _corners[0]

        #     for p in corners:
        #         p = list(map(int, p))
        #         f = cv2.circle(f, p, 3, (0, 0, 255), -1)



from robeex_ai_drone_api import RobeexAIDrone, FrameSize


def main():
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

    if ARUCO_DICT.get(args["type"], None) is None:
        print("[INFO] ArUCo tag of '{}' is not supported".format(
            args["type"]))
        sys.exit(0)

    app_aruco_detector = AppArucoDetector(ARUCO_DICT[args["type"]])

    drone = RobeexAIDrone()
    cap = drone.VideoCapture() if is_using_robeex_cam else cv2.VideoCapture(int(args["cam"]))

    if is_using_robeex_cam:
        # cap.open(frame_size=FrameSize.SIZE_320x240, jpeg_quality=15)
        cap.open(frame_size=FrameSize.SIZE_640x480, jpeg_quality=15)
        # cap.open(frame_size=FrameSize.SIZE_1024x768, jpeg_quality=15)

    print("Waiting for telemetry. Please connect your PC to the drone's Wi-Fi network.")
    drone.wait_for_telemetry()
    print('connecting established !')
    drone.rc.nav.set_mode()
    did_takeoff = False
    while True:
        is_ok, f = cap.read()

        if not is_ok:
            print('frame not ok')
            continue

        app_aruco_detector.detect_tag(f)
        cv2.imshow('frame', f)

        k = cv2.waitKey(1)
        if k == ord('q'):
            break
        if 0:
            if k == ord('l'):
                print('land')
                drone.rc.nav.land(wait_until_done=False)
                did_takeoff = False
            if k == ord('0'):
                print('disarm')
                drone.rc.nav.disarm()
                did_takeoff = False
            if k == ord('1') and not did_takeoff:
                print('takeoff')
                did_takeoff = True
                drone.rc.nav.arm()
                drone.rc.nav.takeoff(1.1, wait_until_done=False)

    cap.release()
    cv2.destroyAllWindows()
    plotter.close()



if __name__ == '__main__':
    main()
