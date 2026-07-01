from robeex_ai_drone_api import RobeexAIDrone, FrameSize
import cv2
from cvzone.FaceDetectionModule import FaceDetector
import time

ENABLE_FLIGHT=1

drone = RobeexAIDrone()
stream = drone.VideoCapture()

stream.open(frame_size=FrameSize.SIZE_640x480, jpeg_quality=16)
# stream.open(frame_size=FrameSize.SIZE_320x240, jpeg_quality=15)
"""
TODO: model selection based on args
"""
face_detector = FaceDetector(0.5, 0)

print('wait for telm ...')
drone.wait_for_telemetry()
print('connecting established !')

drone.rc.nav.set_mode()
did_takeoff = False

last_cmd_time = time.perf_counter()
while stream.isOpened():
    now = time.perf_counter()
    cmd_dt = now - last_cmd_time
    last_cmd_time = now

    success, frame = stream.read()
    if not success or frame is None:
        print('skip')
        continue

    r, faces = face_detector.findFaces(frame)

    if len(faces) > 0:
        drone.rc.rgb.set_full_color(100, 0, 0)

        target = faces[0]
        target_x, target_y = target['center']

        h, w, _ = frame.shape
        frame_center_x = w // 2
        frame_center_y = h // 2

        cv2.line(frame, (frame_center_x, frame_center_y), (target_x, target_y), (0,255,0), 5)
        cv2.line(frame, (frame_center_x, frame_center_y), (target_x, frame_center_y), (0,0,255), 5)
        cv2.line(frame, (frame_center_x, frame_center_y), (frame_center_x, target_y), (255,0,0), 5)


        _, _, w, h = target['bbox']

        # print(w)

        # s_err = 60 - w
        # max_s_vel = 0.20
        # h_vel = max(min((s_err / 200), max_s_vel), -max_s_vel)
        # new_height = drone.rc.telemetry_data.z + h_vel
        # print(f"batt: {drone.rc.telemetry_data.battery}, v: {h_vel:6.3f} + c: {drone.rc.telemetry_data.z:6.3f} = {new_height:6.3f}")
        
        """
        TODO: 
        - we should consider frame size as well
        - P controller shoudl be a decoupled component for each axis (x, y, z, yaw)
        """

        height_err = -(target_y - frame_center_y)
        max_h_vel = 0.40
        h_vel = max(min((height_err / 400), max_h_vel), -max_h_vel)
        new_height = drone.rc.telemetry_data.z + h_vel
        # print(f"batt: {drone.rc.telemetry_data.battery}, v: {h_vel:6.3f} + c: {drone.rc.telemetry_data.z:6.3f} = {new_height:6.3f}")

        # x_err = target_x - frame_center_x
        # max_x_vel = 0.50
        # x_vel = max(min((x_err / 150), max_x_vel), -max_x_vel)
        # new_x = drone.rc.telemetry_data.x + x_vel
        # print(f"batt: {drone.rc.telemetry_data.battery}, v: {x_vel:6.3f} + c: {drone.rc.telemetry_data.x:6.3f} = {new_x:6.3f}")

        yaw_err = target_x - frame_center_x 
        # yaw_vel = err * (1/70) * cmd_dt
        yaw_vel = max(min(yaw_err / 480, 4),-4)
        current_yaw = drone.rc.telemetry_data.wz
        new_yaw = current_yaw + yaw_vel

        # height_err = -(target_y - frame_center_y)
        # max_h_vel = 0.20
        # h_vel = max(min((height_err / 200), max_h_vel), -max_h_vel)
        # new_height = drone.rc.telemetry_data.z + h_vel

        # print(f"batt: {drone.rc.telemetry_data.battery}, h: {h_vel:6.3f} + c: {drone.rc.telemetry_data.z:6.3f} = {new_height:6.3f}")
        print(f"batt: {drone.rc.telemetry_data.battery}, v: {h_vel:6.3f} + c: {drone.rc.telemetry_data.z:6.3f} = {new_height:6.3f}")
        # print(f"batt: {drone.rc.telemetry_data.battery}, v: {yaw_vel:6.3f} + c: {drone.rc.telemetry_data.wz:6.3f} = {new_yaw:6.3f}")
        if did_takeoff:
            drone.rc.nav.set_yaw(new_yaw, wait_until_done=False)
            drone.rc.nav.set_altitude(new_height, wait_until_done=False)
            # drone.rc.nav.set_position_3d(new_x, drone.rc.telemetry_data.y, new_height, wait_until_done=False)
    else:
        print(f"batt: {drone.rc.telemetry_data.battery}, v: {0:6.3f} + c: {drone.rc.telemetry_data.z:6.3f} = {0:6.3f}")
        drone.rc.rgb.set_full_color(0,100,0)

    cv2.imshow('RoBeeX Feed', frame)
    k = cv2.waitKey(1)
    if k == ord('q'):
        break
    if ENABLE_FLIGHT:
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

stream.release()
cv2.destroyAllWindows()
