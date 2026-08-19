"""Control the mouse with the pitch, yaw, and roll of a RoBeeX AI Drone."""

import math
import time

import pyautogui
from robeex_ai_drone_api import RobeexAIDrone


POINTER_ANGLE_LIMIT_DEGREES = 50.0
MOVEMENT_DEAD_ZONE_DEGREES = 2.0
SMOOTHING_TIME_SECONDS = 0.10
CLICK_ROLL_THRESHOLD_DEGREES = 30.0
CLICK_RELEASE_THRESHOLD_DEGREES = 20.0
EXIT_YAW_DEGREES = 180.0

# Moving the pointer to the top-left corner remains an emergency stop.
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(value, upper))


def wrapped_angle_delta(current_angle: float, previous_angle: float) -> float:
    """Return the shortest signed delta between two angles in radians."""
    return (current_angle - previous_angle + math.pi) % (2 * math.pi) - math.pi


def apply_dead_zone(angle_degrees: float) -> float:
    """Remove small movements and preserve the full range outside the dead zone."""
    magnitude = abs(angle_degrees)
    if magnitude <= MOVEMENT_DEAD_ZONE_DEGREES:
        return 0.0

    adjusted_magnitude = (
        (magnitude - MOVEMENT_DEAD_ZONE_DEGREES)
        * POINTER_ANGLE_LIMIT_DEGREES
        / (POINTER_ANGLE_LIMIT_DEGREES - MOVEMENT_DEAD_ZONE_DEGREES)
    )
    return math.copysign(adjusted_magnitude, angle_degrees)


def smoothing_factor(elapsed_seconds: float) -> float:
    """Return a frame-rate-independent exponential interpolation factor."""
    return 1 - math.exp(-elapsed_seconds / SMOOTHING_TIME_SECONDS)


def interpolate(current: float, target: float, factor: float) -> float:
    return current + (target - current) * factor


def angle_to_screen_position(
    yaw_degrees: float,
    pitch_degrees: float,
    screen_width: int,
    screen_height: int,
) -> tuple[float, float]:
    """Map pitch and yaw angles to an absolute position on the screen."""
    yaw = clamp(
        apply_dead_zone(yaw_degrees),
        -POINTER_ANGLE_LIMIT_DEGREES,
        POINTER_ANGLE_LIMIT_DEGREES,
    )
    pitch = clamp(
        apply_dead_zone(pitch_degrees),
        -POINTER_ANGLE_LIMIT_DEGREES,
        POINTER_ANGLE_LIMIT_DEGREES,
    )
    center_x = screen_width / 2
    center_y = screen_height / 2
    return (
        center_x * (1 + yaw / POINTER_ANGLE_LIMIT_DEGREES),
        center_y * (1 + pitch / POINTER_ANGLE_LIMIT_DEGREES),
    )


def update_click_state(roll_degrees: float, click_is_armed: bool) -> bool:
    """Click once per roll gesture and re-arm after returning near level."""
    if click_is_armed:
        if roll_degrees <= -CLICK_ROLL_THRESHOLD_DEGREES:
            pyautogui.click(button="left")
            return False
        if roll_degrees >= CLICK_ROLL_THRESHOLD_DEGREES:
            pyautogui.click(button="right")
            return False
    elif abs(roll_degrees) <= CLICK_RELEASE_THRESHOLD_DEGREES:
        return True

    return click_is_armed


def control_mouse() -> None:
    drone = RobeexAIDrone()

    print("Waiting for drone connection...")
    drone.wait_for_telemetry()
    previous_yaw = drone.rc.telemetry_data.wz
    accumulated_yaw = 0.0
    screen_width, screen_height = pyautogui.size()
    smoothed_x, smoothed_y = pyautogui.position()
    previous_update_time = time.monotonic()
    click_is_armed = True

    print(
        "Connected. Use pitch/yaw to move, roll left/right to click, "
        "or rotate yaw 180 degrees to exit."
    )

    try:
        while True:
            telemetry = drone.rc.get_next_telemetry_update()
            accumulated_yaw += wrapped_angle_delta(telemetry.wz, previous_yaw)
            previous_yaw = telemetry.wz
            yaw_degrees = math.degrees(accumulated_yaw)

            if abs(yaw_degrees) >= EXIT_YAW_DEGREES:
                print("Yaw reached 180 degrees. Exiting...")
                break

            pitch_degrees = -math.degrees(telemetry.pitch)
            roll_degrees = math.degrees(telemetry.roll)
            target_x, target_y = angle_to_screen_position(
                yaw_degrees, pitch_degrees, screen_width, screen_height
            )

            current_time = time.monotonic()
            factor = smoothing_factor(current_time - previous_update_time)
            previous_update_time = current_time
            smoothed_x = interpolate(smoothed_x, target_x, factor)
            smoothed_y = interpolate(smoothed_y, target_y, factor)

            pyautogui.moveTo(smoothed_x, smoothed_y)
            click_is_armed = update_click_state(roll_degrees, click_is_armed)
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        drone.rc.stop()


if __name__ == "__main__":
    control_mouse()
