from time import sleep
import math
from robeex_ai_drone_api import RobeexAIDrone, RGBMode

drone = RobeexAIDrone()

def circle():
    drone.rc.nav.set_position_2d(1, 0)
    for angle in range(360):
        rad = math.radians(angle)

        x, y = math.cos(rad), math.sin(rad)

        print(f"{x:5.2f}, {y:5.2f}")

        drone.rc.nav.set_position_2d(x, y, wait_until_done=False)
        drone.rc.nav.set_yaw(-rad, wait_until_done=False)

        sleep(0.05)


def flight():
    drone.rc.nav.set_mode()
    drone.rc.nav.arm()
    sleep(0.5)
    print('takeoff -- start')
    drone.rc.nav.takeoff(1)
    print('takeoff -- done')
    
    sleep(1)

    circle() 

    sleep(1)
    drone.rc.nav.set_position_2d(0, 0)
    print('landing -- start')
    drone.rc.nav.land()
    print('landing -- done')
    sleep(1)
    drone.rc.nav.disarm()

def main():
    print("Waiting for telemetry. Please connect your PC to the drone's Wi-Fi network.")
    drone.wait_for_telemetry()
    print('connecting established !')

    # drone.rc.rgb.set_full_color(100, 0, 255)
    # sleep(10)
    # circle()
    flight();

if __name__ == "__main__":
    main()
