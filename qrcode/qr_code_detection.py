import cv2
import numpy as np
import argparse
from robeex_ai_drone_api import RobeexAIDrone

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cam", type=str,
        default="robeex",
        help="Camera")

    return vars(ap.parse_args())

class QRDetector:
    def __init__(self):
        self.detector = cv2.QRCodeDetector()

    def process_frame(self, frame):
        detected, decoded_info, corners, _ = self.detector.detectAndDecodeMulti(frame)

        if not detected or corners is None:
            return frame

        for data, qr_corners in zip(decoded_info, corners):
            image_points = qr_corners.reshape(4, 2).astype(np.float32)
            center_x, center_y = map(int, np.mean(image_points, axis=0))

            boundary = image_points.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(
                frame,
                [boundary],
                isClosed=True,
                color=(0, 255, 0),
                thickness=2,
            )
            cv2.circle(frame, (center_x, center_y), 5, (0, 0, 255), -1)
            cv2.putText(
                frame,
                f"Center: ({center_x}, {center_y})",
                (center_x + 8, center_y - 8),
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
                    tuple(map(int, image_points[0])),
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

pose_detector = QRDetector()

drone = RobeexAIDrone()
camera = drone.VideoCapture() if is_using_robeex_cam else cv2.VideoCapture(int(args["cam"]))

while True:
    ok, frame = camera.read()
    if not ok:
        continue

    frame = pose_detector.process_frame(frame)
    cv2.imshow("QR Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

camera.release()
cv2.destroyAllWindows()
