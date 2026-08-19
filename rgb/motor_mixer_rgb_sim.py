from robeex_ai_drone_api import RobeexAIDrone, MotorNumber
import math

drone = RobeexAIDrone()

def calc_mixer(t, r, p):
    z = [t + p - r, t + p + r,t - p + r, t - p - r]
    return tuple(map(lambda x: int(max(x, 0)), z))


def main():
    print("Waiting for telemetry. Please connect your PC to the drone's Wi-Fi network.")
    drone.wait_for_telemetry()
    print('connecting established !')

    while True:
        telm = drone.rc.get_next_telemetry_update()

        r, p = 250 * (telm.roll / math.pi), 250 * (telm.pitch / math.pi)
        motors = ul, ur, dl, dr = calc_mixer(20, r, p)

        print(f"UL: {ul:3.0f} UR: {ur:3.0f} DR: {dr:3.0f} DL: {dl:3.0f}")

        for i, m in enumerate(motors):
            drone.rc.rgb.set_color_by_motor_number(m, 100 - m, 0, MotorNumber(i + 1))

if __name__ == "__main__":
    main()
