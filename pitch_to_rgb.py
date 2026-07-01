from robeex_ai_drone_api import RobeexAIDrone
import math

def main():
    drone = RobeexAIDrone()

    print('wait for telm ...')
    drone.wait_for_telemetry()
    print('connecting established !')

    try:
        while True:
            telemetry = drone.rc.get_next_telemetry_update()

            if telemetry is None:
                continue

            pg = (telemetry.pitch/(math.pi/2))
            if pg > 0:
                drone.rc.rgb.set_full_color(255 * pg , (1 - pg) * 255, 0)
            print(f"Telemetry: {telemetry.pitch} => {pg}")
    except Exception as e:
        print(e)
        print("Stopping...")

if __name__ == "__main__":
    main()

