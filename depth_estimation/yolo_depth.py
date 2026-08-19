import argparse
import time
import cv2
import torch
from robeex_ai_drone_api import FrameSize, RobeexAIDrone
from ultralytics import YOLO

def parse_args():
    parser = argparse.ArgumentParser(description="Run real-time depth estimation.")
    parser.add_argument(
        "-c", "--cam",
        action="store_true",
        help="Use the local webcam instead of the Robeex camera.",
    )
    return parser.parse_args()


args = parse_args()

# 1. Determine GPU device
if torch.cuda.is_available():
    device = 0
    print("Using GPU (CUDA)")
elif torch.backends.mps.is_available():
    device = 'mps'
    print("Using Apple Silicon GPU (MPS)")
else:
    device = 'cpu'
    print("Using CPU")

# 2. Load the native YOLO Depth model
model = YOLO("yolo26n-depth.pt")

# 3. Initialize the selected camera stream (Robeex by default)
if args.cam:
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
else:
    drone = RobeexAIDrone()
    print("Waiting for telemetry. Please connect your PC to the drone's Wi-Fi network.")
    drone.wait_for_telemetry()
    cap = drone.VideoCapture()
    cap.open(FrameSize.SIZE_640x480, 16)

prev_time = time.time()

print("Starting stream... Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    # 4. Run inference on GPU
    # Use 'quantize' instead of the deprecated 'half' for FP16 speed boost on CUDA
    quant_mode = "fp16" if torch.cuda.is_available() else None
    results = model(frame, device=device, quantize=quant_mode, verbose=False)[0]

    # 5. Extract depth tensor back to CPU / NumPy
    depth_array = results.depth.data.squeeze().cpu().numpy()

    # 6. Normalize and map to color for live display
    depth_visual = cv2.normalize(depth_array, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
    depth_colored = cv2.applyColorMap(depth_visual, cv2.COLORMAP_INFERNO)
    # depth_colored = max(255 - depth_visual, )

    # 7. Calculate FPS & Center Distance
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    h, w = depth_array.shape
    center_dist = depth_array[h // 2, w // 2]

    # Overlay UI telemetry onto camera frame
    cv2.putText(frame, f"FPS: {int(fps)}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    cv2.putText(frame, f"Center Dist: {center_dist:.2f}m", (20, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Target reticle at frame center
    cv2.circle(frame, (w // 2, h // 2), 5, (0, 0, 255), -1)

    # 8. Display output streams
    cv2.imshow("Webcam Feed", frame)
    cv2.imshow("Realtime Depth Vis", depth_visual)
    cv2.imshow("Realtime Depth Color", depth_colored)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
