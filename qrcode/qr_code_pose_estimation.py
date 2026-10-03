import cv2
import numpy as np
import argparse
from robeex_ai_drone_api import RobeexAIDrone

QR_SIZE_METER = 0.115 # 11.5 cm
AXIS_LENGTH_METER = 0.0575  # 5.75 cm

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cam", type=str,
        default="robeex",
        help="Camera")

    return vars(ap.parse_args())

class QRPoseDetector:
    def __init__(self, calibration_path):
        self.calib = np.load(calibration_path)

        self.mtx = self.calib["mtx"]
        self.dist = self.calib["dist"]

        self.detector = cv2.QRCodeDetector()

        half = QR_SIZE_METER / 2.0

        # top-left, top-right, bottom-right, bottom-left
        self.object_points = np.array(
            [
                [-half,  half, 0.0],
                [ half,  half, 0.0],
                [ half, -half, 0.0],
                [-half, -half, 0.0],
            ],
            dtype=np.float32,
        )

    def process_frame(self, frame):
        detected, decoded_info, corners, _ = self.detector.detectAndDecodeMulti(frame)

        if not detected or corners is None:
            return frame

        for index, (data, qr_corners) in enumerate(zip(decoded_info, corners)):
            image_points = qr_corners.reshape(4, 2).astype(np.float32)

            boundary = image_points.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(
                frame,
                [boundary],
                isClosed=True,
                color=(0, 255, 0),
                thickness=2,
            )

            pose_ok, rvec, tvec = cv2.solvePnP(
                self.object_points,
                image_points,
                self.mtx,
                self.dist,
                flags=cv2.SOLVEPNP_IPPE_SQUARE,
            )

            if not pose_ok:
                continue

            cv2.drawFrameAxes(
                frame,
                self.mtx,
                self.dist,
                rvec,
                tvec,
                AXIS_LENGTH_METER,
                3,
            )

            # Camera-coordinate position, converted from metres to centimetres.
            x_cm, y_cm, z_cm = tvec.reshape(3) * 100.0
            distance_cm = np.linalg.norm(tvec) * 100.0
            label_x = int(image_points[:, 0].min())
            label_y = int(image_points[:, 1].min()) - 10

            label = (
                f"QR {index + 1}: X {x_cm:+.1f}, Y {y_cm:+.1f}, "
                f"Z {z_cm:.1f}, D {distance_cm:.1f} cm"
            )
            cv2.putText(
                frame,
                label,
                (label_x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 255),
                2,
            )

            if data:
                print(f'data[len={len(data)}]="{data}"')
                cv2.putText(
                    frame,
                    f"QR: {data}",
                    (label_x, label_y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 0),
                    2,
                )

        return frame



args = parse_args()

is_using_robeex_cam = False
if args["cam"] == "robeex":
    is_using_robeex_cam = True

# WARN: you should calibrate the camera by yourself and change this path to your calibration data file.
# WARN: if you use the calibration data file in this repo, the pose estimation may be inaccurate.
CALIBRATION_PATH = "april_tag/" + ('calibration_data_robeex.npz' if is_using_robeex_cam else 'calibration_data_pc.npz')

pose_detector = QRPoseDetector(CALIBRATION_PATH)

drone = RobeexAIDrone()
camera = drone.VideoCapture() if is_using_robeex_cam else cv2.VideoCapture(int(args["cam"]))

while True:
    ok, frame = camera.read()
    if not ok:
        continue

    frame = pose_detector.process_frame(frame)
    cv2.imshow("QR pose", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

camera.release()
cv2.destroyAllWindows()
