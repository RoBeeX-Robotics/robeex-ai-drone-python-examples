import pyautogui
import time
from robeex_ai_drone_api import RobeexAIDrone
from math import pi

print('?')

# Configure PyAutoGUI for speed and safety
pyautogui.FAILSAFE = True  # Slam mouse to top-left corner to emergency stop
pyautogui.PAUSE = 0        # Remove the default 0.1s delay for smoother movement

def control_mouse():
    drone = RobeexAIDrone()
    
    print("Waiting for drone connection...")
    drone.wait_for_telemetry()
    print("Connected! Tilt the drone to move the mouse.")

    try:
        init_yaw = drone.rc.telemetry_data.wz
        is_pitch_rotated = False
        w, h = pyautogui.size()
        center_x, center_y = w // 2, h // 2


        while True:
            # The library provides telemetry through drone.telem
            # Verify if your specific version uses .roll or .attitude['roll']
            # Based on standard Robeex API structure:
            # telem_data = drone.rc.get_next_telemetry_update()
            telem_data = drone.rc.telemetry_data
            
            # roll = (telem_data.roll / pi) * 180
            pitch = -(telem_data.pitch / pi) * 180
            yaw = telem_data.wz - init_yaw
            yaw = (yaw / pi) * 180

            # 1. Deadzone: Ignore noise when the drone is mostly level
            # if abs(roll) < 2 and abs(pitch) < 2:
                # time.sleep(0.01)
                # continue

            # pitch_at_thr = abs(pitch) > 30
            # if pitch_at_thr and not is_pitch_rotated:
            #     is_pitch_rotated = True
            #     print('click', 'right' if pitch > 0 else 'left')
            # elif not pitch_at_thr and is_pitch_rotated:
            #     print('mouse up')
            
            angular_freedom = 50

            yaw = max(-angular_freedom, min(yaw, angular_freedom))
            pitch = max(-angular_freedom, min(pitch, angular_freedom))

            # 2. Sensitivity: Adjust these multipliers to change speed
            # Pitch is often inverted: tilt forward (positive) should move mouse down (positive Y)
            target_x = (center_x * (yaw / angular_freedom)) + (center_x)
            target_y = (center_y * (pitch / angular_freedom)) + (center_y)

            # 3. Move the mouse relative to its current position
            # if not pitch_at_thr:
                # pyautogui.moveRel(move_x, move_y)
            print(f"deg: [x = {yaw:5.2f}, y = {pitch:5.2f}] --> move [x = {target_x:5.2f}, y = {target_y:5.2f}]")
            if not (target_x == 0 and target_y == 0):
                pyautogui.moveTo(target_x, target_y, 0.1)

            # 4. Small delay to prevent CPU maxing out
            time.sleep(0.01)

    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    control_mouse()
