import cv2
from cv2.typing import MatLike
import argparse
import sys
import numpy as np
from time import time
from app_aruco_detector import ARUCO_DICT, AppArucoDetector
from ws_server import BroadcastServer
import math

from robeex_ai_drone_api import RobeexAIDrone, FrameSize, UDPVideoStream

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("-mt", "--multi-tag", type=bool,
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Publish Multiple AR Tags")
    ap.add_argument("-c", "--cam", type=str,
        default="robeex",
        help="Camera")
    ap.add_argument("-t", "--type", type=str,
        default="DICT_5X5_100",
        help="type of ArUCo tag to generate")

    return vars(ap.parse_args())

args = parse_args()

is_using_robeex_cam = False
if args["cam"] == "robeex":
    is_using_robeex_cam = True


def main():
    cv2.namedWindow('frame', cv2.WINDOW_NORMAL)

    if ARUCO_DICT.get(args["type"], None) is None:
        print("[INFO] ArUCo tag of '{}' is not supported".format(
            args["type"]))
        sys.exit(0)


    telm_server = BroadcastServer(8686)
    telm_server.start()

    tag_server = BroadcastServer(8687)
    tag_server.start()

    app_aruco_detector = AppArucoDetector('calibration_data_robeex.npz' if is_using_robeex_cam else 'calibration_data_pc.npz', ARUCO_DICT[args["type"]])

    drone = RobeexAIDrone()
    cap = drone.VideoCapture() if is_using_robeex_cam else cv2.VideoCapture(int(args["cam"]))

    if is_using_robeex_cam and isinstance(cap, UDPVideoStream):
        # cap.open(frame_size=FrameSize.SIZE_320x240, jpeg_quality=15)
        cap.open(frame_size=FrameSize.SIZE_640x480, jpeg_quality=8)
        # cap.open(frame_size=FrameSize.SIZE_1024x768, jpeg_quality=15)

    if is_using_robeex_cam:
        print('wait for telm ...')
        drone.wait_for_telemetry()
        print('connecting established !')
        drone.rc.nav.set_mode()

    did_takeoff = False

    while True:
        is_ok, f = cap.read()

        if not is_ok or f is None:
            print('frame not ok')
            continue

        if is_using_robeex_cam:
            telm_server.broadcast(drone.rc.telemetry_data.json)
        r = app_aruco_detector.detect_tag(f)
        if len(r) > 0:
            tag = r[0]

            # print(f"Marker {tag['id']} position: x: {tag['pos'][0]:5.2f}, y: {tag['pos'][1]:5.2f}, z: {tag['pos'][2]:5.2f} " + \
            #     f"--- r: {tag['rot'][0]:7.1f}, p: {tag['rot'][1]:7.2f}, y: {tag['rot'][2]:7.2f}")
            # print(tag)
            if args['multi_tag']:
                tag_server.broadcast_json(r)
            else:
                tag_server.broadcast_json(tag)

        cv2.imshow('frame', f)

        k = cv2.waitKey(1)
        if k == ord('.'):
            break
        if is_using_robeex_cam and 0:
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
            t = drone.rc.telemetry_data
            s = 0.15
            if k == ord('w'):
                drone.rc.nav.set_position_3d(t.x, t.y + s, t.z, False)
            if k == ord('a'):
                drone.rc.nav.set_position_3d(t.x - s, t.y, t.z, False)
            if k == ord('d'):
                drone.rc.nav.set_position_3d(t.x + s, t.y, t.z, False)
            if k == ord('s'):
                drone.rc.nav.set_position_3d(t.x, t.y - s, t.z, False)

            s = 0.05
            if k == ord(']'):
                drone.rc.nav.set_position_3d(t.x, t.y, t.z + s, False)
            if k == ord('['):
                drone.rc.nav.set_position_3d(t.x, t.y, t.z - s, False)

            wz_s = (5 / 180) * math.pi 
            if k == ord('q'):
                drone.rc.nav.set_yaw(t.wz - wz_s, False)
            if k == ord('e'):
                drone.rc.nav.set_yaw(t.wz + wz_s, False)
        elif k == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
