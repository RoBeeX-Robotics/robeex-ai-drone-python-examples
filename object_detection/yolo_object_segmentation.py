import argparse
import cv2
from robeex_ai_drone_api import FrameSize, RobeexAIDrone
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Run real-time YOLO object segmentation.")
    parser.add_argument(
        "-c", "--cam", action="store_true",
        help="Use the local webcam instead of the Robeex camera.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Load the latest SOTA segmentation model (NMS-free end-to-end inference)
    # Options for YOLO26: yolo26n-seg.pt (Nano), yolo26s-seg.pt (Small),
    # yolo26m-seg.pt (Medium), yolo26l-seg.pt (Large)
    # Options for YOLO11: yolo11n-seg.pt, yolo11s-seg.pt, yolo11m-seg.pt,
    # yolo11l-seg.pt
    model = YOLO("yolo26l-seg.pt")

    # Open the selected camera stream (Robeex by default)
    if args.cam:
        cap = cv2.VideoCapture(0)
    else:
        drone = RobeexAIDrone()
        print("Waiting for telemetry. Please connect your PC to the drone's Wi-Fi network.")
        drone.wait_for_telemetry()
        cap = drone.VideoCapture()
        cap.open(FrameSize.SIZE_640x480, 16)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Set camera resolution (optional: 1280x720)
    # cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    # cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    print("Press 'q' to exit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            continue

        # Run inference using stream=True for optimized memory usage during live video
        results = model(frame, device="cuda", stream=True, conf=0.45)

        # Draw boxes and labels onto frame
        for result in results:
            annotated_frame = result.plot()

        # Display result
        cv2.imshow("YOLO Real-Time Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
