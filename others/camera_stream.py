import cv2
from robeex_ai_drone_api import RobeexAIDrone, FrameSize
import argparse
import time

def parse_args():
    parser = argparse.ArgumentParser(
        description="RoBeeX Drone video stream viewer with configurable frame size and JPEG quality."
    )

    parser.add_argument(
        "-f", "--frame_size",
        type=int,
        choices=range(4, 14),
        default=7,
        help="Frame size (integer 4–11). Corresponds to FrameSize enum values.",
        metavar="[4-11]"
    )

    parser.add_argument(
        "-q", "--jpeg_quality",
        type=int,
        choices=range(1, 64),
        default=15,
        help="JPEG quality (1–63). Lower is higher compression.",
        metavar="[1-63]"
    )

    parser.add_argument(
        "--blur",
        action="store_true",
        help="Apply median and Gaussian blur to video frames."
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # --- Initialize drone and stream ---
    drone = RobeexAIDrone()
    stream = drone.VideoCapture()

    print("Wait for telemetry ...")
    drone.wait_for_telemetry()

    # Map frame_size integer to FrameSize enum
    frame_size_enum = FrameSize(args.frame_size)

    stream.open(frame_size=frame_size_enum, jpeg_quality=args.jpeg_quality)
    print(f"Opened stream with frame_size={frame_size_enum.name}, jpeg_quality={args.jpeg_quality}")

    # --- Display video feed ---
    bad_count = 0
    total_count = 0
    last_report = time.time()
    avg_packet_loss = 0

    started_at = time.time()

    # TEST_TIME_S = 10
    # while stream.isOpened() and time.time() - started_at < TEST_TIME_S:
    while stream.isOpened():
        success, frame = stream.read()
        total_count += 1

        if not success:
            bad_count += 1
            continue

        if args.blur:
            frame = cv2.medianBlur(frame, 9)
            frame = cv2.GaussianBlur(frame, (7, 7), 0)

        # Report packet loss every 1 second
        now = time.time()
        if now - last_report >= 1:
            loss_percent = (bad_count / total_count) * 100 if total_count > 0 else 0
            print(f"Packet Loss: {bad_count:3.0f}/{total_count:3.0f} ({loss_percent:.1f}%)")
            # avg_packet_loss += (1/TEST_TIME_S) * loss_percent
            bad_count = 0
            total_count = 0
            last_report = now

        cv2.imshow("RoBeeX Feed", frame)
        if cv2.waitKey(1) == ord("q"):
            break

    # print(f"Average Packet Loss: ({avg_packet_loss:.1f}%)")
    stream.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
