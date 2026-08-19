import pickle
import argparse
import numpy as np
import cv2
from robeex_ai_drone_api import RobeexAIDrone
import asyncio


def parse_args():
    parser = argparse.ArgumentParser(description="Parse pickle file path.")
    parser.add_argument('pickle_path', type=str, help="Path to the pickle file.")
    parser.add_argument('--flight', default=False, action=argparse.BooleanOptionalAction)
    return parser.parse_args()

REAL_TO_CV_SCALE = 100
OFFSET_X = 256
OFFSET_Y = 128

def to_real_pos(xc, yc):
    return (xc / REAL_TO_CV_SCALE, yc / REAL_TO_CV_SCALE)

def to_cv_pos(xm, ym):
    return (int(xm * REAL_TO_CV_SCALE), int(ym * REAL_TO_CV_SCALE))

async def flight(ctx, do_flight):
    # Create an image for visualization.
    img = np.ones((512, 512, 3), dtype=np.uint8) * 255
    w, h, _ = img.shape
    # Draw a vertical line to show the OFFSET_X
    img = cv2.line(img, (OFFSET_X, 0), (OFFSET_X, h), (0, 0, 255), 1)
    img = cv2.line(img, (0, h - OFFSET_Y), (w, h - OFFSET_Y), (0, 0, 255), 1)

    print('Hi')
    drone = RobeexAIDrone()

    if do_flight:
        await drone.rc.nav.disarm()
        print("Waiting for telemetry. Please connect your PC to the drone's Wi-Fi network.")
        await drone.wait_for_telemetry()
        print('done')
        await drone.rc.nav.disarm()

    cv2.imshow(f"Y", img)
    drone.rc.rgb.set_full_color(100, 100, 100)

    if do_flight:
        if cv2.waitKey(0) != ord('a'):
            return
        drone.rc.rgb.set_full_color(200, 0, 0)
        await drone.rc.nav.arm()
        if cv2.waitKey(0) != ord('t'):
            return
        drone.rc.rgb.set_full_color(0, 255, 0)
        await drone.rc.nav.takeoff(0.5)

    drone.rc.rgb.set_full_color(0, 0, 200)
    for i in range(len(ctx)):
        print(i)

        xp, yp = ctx[i]
        cv2.circle(img, (OFFSET_X + xp,  h - yp - OFFSET_Y), 1, (100, 0, 100), -1)
        xm, ym = to_real_pos(xp,yp)
        # print(xp,yp, '=>', xm, ym)
        
        drone_pos = (float(xm), 0, float(ym) + 0.5)
        print(drone_pos)
        if do_flight:
            await drone.rc.nav.set_position_3d(*drone_pos)

        # _ctx = ctx[:i]
        # for x, y in _ctx:
        #     cv2.circle(img, (x, char_h - y), 1, (100, 0, 255), -1)

        cv2.imshow(f"Y", img)
        k = cv2.waitKey(100) & 0xFF
        if k == ord('0'):
            await drone.rc.nav.disarm()
            break
        if k == ord('q'):
            break

    if do_flight:
        await drone.rc.nav.land()
    while cv2.waitKey(0) != ord('q'):
        pass
    cv2.destroyAllWindows()

def main():
    args = parse_args()
    if args.flight and input('Are you sure you want to fly ?').lower() != 'y':
        return
    with open(args.pickle_path, 'rb') as f:
        ctx = pickle.load(f)
        ctx = np.array([to_cv_pos(x, y) for x, y in ctx])
        print(ctx)
        asyncio.run(flight(ctx, args.flight)) 

if __name__ == "__main__":
    main()
