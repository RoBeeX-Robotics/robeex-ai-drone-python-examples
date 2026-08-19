import argparse
import cv2
import numpy as np
import open3d as o3d
import torch
from robeex_ai_drone_api import FrameSize, RobeexAIDrone
from ultralytics import YOLO


def parse_args():
    parser = argparse.ArgumentParser(description="Run real-time YOLO depth voxel mapping.")
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

    # 2. UPGRADE: Load Medium YOLO-Depth Model for higher fidelity
    print("Loading high-fidelity depth model...")
    model = YOLO("yolo26l-depth.pt")  # Upgraded from 'n' (nano) to 'm' (medium)



    width, height = 640, 480
    # 3. Open the selected camera stream (Robeex by default)
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
    vis.create_window("Live Real-Time Voxel Map", width=1024, height=768)

    # Define intrinsic camera parameters
    focal_length = max(width, height)
    intrinsic = o3d.camera.PinholeCameraIntrinsic(
        width, height, focal_length, focal_length, width / 2.0, height / 2.0
    )

    is_geometry_added = False
    prev_voxel_grid = None

    print("Starting real-time Voxel map... Press 'q' in OpenCV window to stop.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 5. Run Depth Inference
        quant_mode = "fp16" if torch.cuda.is_available() else None
        results = model(frame, device=device, quantize=quant_mode, verbose=False)[0]

        # Extract depth map array in meters
        depth_array = results.depth.data.squeeze().cpu().numpy()

        if depth_array.shape != (height, width):
            depth_array = cv2.resize(depth_array, (width, height), interpolation=cv2.INTER_NEAREST)

        # 6. Build RGB-D Image & 3D Point Cloud
        o3d_color = o3d.geometry.Image(rgb_frame)
        o3d_depth = o3d.geometry.Image(depth_array.astype(np.float32))

        # depth_trunc prevents mapping the sky or distant background noise
        rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d_color, o3d_depth, depth_scale=1.0, depth_trunc=8.0, convert_rgb_to_intensity=False
        )

        new_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(rgbd_image, intrinsic)

        # Flip coordinate system to render upright
        new_pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

        # 7. UPGRADE: Convert Point Cloud to Voxel Grid (Occupancy Map)
        # voxel_size=0.05 creates 5x5x5 cm physical blocks.
        voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(new_pcd, voxel_size=0.01)

        # 8. Update 3D Geometry dynamically
        if not is_geometry_added:
            vis.add_geometry(voxel_grid)
            is_geometry_added = True
        else:
            # Unlike point clouds, VoxelGrids must be swapped to update safely in the UI
            vis.remove_geometry(prev_voxel_grid, reset_bounding_box=False)
            vis.add_geometry(voxel_grid, reset_bounding_box=False)

        prev_voxel_grid = voxel_grid

        # Render updated 3D frame
        vis.poll_events()
        vis.update_renderer()

        # Show 2D camera feed with basic telemetry
        cv2.putText(frame, f"Model: YOLO26m-Depth", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Camera Feed (2D)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Clean up resources
    cap.release()
    cv2.destroyAllWindows()
    vis.destroy_window()

if __name__ == "__main__":
    main()
