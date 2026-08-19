import argparse
import cv2
import numpy as np
import open3d as o3d
import torch
from robeex_ai_drone_api import FrameSize, RobeexAIDrone
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Run real-time YOLO depth point-cloud mapping.")
    parser.add_argument(
        "-c", "--cam", action="store_true",
        help="Use the local webcam instead of the Robeex camera.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Determine Device
    if torch.cuda.is_available():
        device = 0
        print("Using GPU (CUDA)")
    elif torch.backends.mps.is_available():
        device = "mps"
        print("Using Apple Silicon GPU (MPS)")
    else:
        device = "cpu"
        print("Using CPU")

    # 2. Load Lightweight Metric Depth Model for Real-Time Performance
    print("Loading depth model...")
    model = YOLO("yolo26l-depth.pt")

    # 3. Open the selected camera stream (Robeex by default)
    width, height = 640, 480
    if args.cam:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    else:
        drone = RobeexAIDrone()
        drone.wait_for_telemetry()
        cap = drone.VideoCapture()
        cap.open(FrameSize.SIZE_640x480, 16)

    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # 4. Setup Open3D Non-Blocking Visualizer Window
    vis = o3d.visualization.Visualizer()
    vis.create_window("Live Real-Time 3D Map", width=1024, height=768)

    # Define intrinsic camera parameters for 3D projection
    focal_length = max(width, height)
    intrinsic = o3d.camera.PinholeCameraIntrinsic(
        width,
        height,
        focal_length,
        focal_length,
        width / 2.0,
        height / 2.0,
    )

    # Create an initial empty point cloud object
    pcd = o3d.geometry.PointCloud()
    is_pcd_added = False

    print("Starting real-time 3D map... Press 'q' in OpenCV window to stop.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert OpenCV frame (BGR) to RGB for Open3D
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 5. Run Depth Inference on GPU
        # quantize='fp16' enables FP16 speed boost on NVIDIA GPUs
        quant_mode = "fp16" if torch.cuda.is_available() else None
        results = model(
            frame, device=device, quantize=quant_mode, verbose=False
        )[0]

        # Extract depth map array in meters
        depth_array = results.depth.data.squeeze().cpu().numpy()

        # Ensure depth map matches camera frame dimensions
        if depth_array.shape != (height, width):
            depth_array = cv2.resize(
                depth_array, (width, height), interpolation=cv2.INTER_NEAREST
            )

        # 6. Build RGB-D Image & 3D Point Cloud
        o3d_color = o3d.geometry.Image(rgb_frame)
        o3d_depth = o3d.geometry.Image(
            depth_array.astype(np.float32)
        )  # Float32 meters

        rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d_color,
            o3d_depth,
            depth_scale=1.0,  # 1.0 because values are already in meters
            depth_trunc=10.0,  # Truncate points beyond 10 meters for cleaner rendering
            convert_rgb_to_intensity=False,
        )

        # Generate new point cloud for the current frame
        new_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
            rgbd_image, intrinsic
        )

        # Flip coordinate system to orient upright in Open3D
        new_pcd.transform(
            [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]
        )

        # 7. Update 3D Geometry in Real-Time
        pcd.points = new_pcd.points
        pcd.colors = new_pcd.colors

        if not is_pcd_added:
            vis.add_geometry(pcd)
            is_pcd_added = True
        else:
            vis.update_geometry(pcd)

        # Render updated 3D frame
        vis.poll_events()
        vis.update_renderer()

        # Show 2D camera feed with depth indicator
        center_dist = depth_array[height // 2, width // 2]
        cv2.putText(
            frame,
            f"Center Distance: {center_dist:.2f}m",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
        )
        cv2.circle(frame, (width // 2, height // 2), 5, (0, 0, 255), -1)
        cv2.imshow("Camera Feed (2D)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Clean up resources
    cap.release()
    cv2.destroyAllWindows()
    vis.destroy_window()


if __name__ == "__main__":
    main()
