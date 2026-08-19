import argparse
import cv2
import numpy as np
import open3d as o3d
import torch
from robeex_ai_drone_api import FrameSize, RobeexAIDrone
from transformers import AutoImageProcessor, AutoModelForDepthEstimation


def parse_args():
    parser = argparse.ArgumentParser(description="Run real-time Depth Anything 3D mapping.")
    parser.add_argument(
        "-c", "--cam", action="store_true",
        help="Use the local webcam instead of the Robeex camera.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 1. Setup GPU Device
    if torch.cuda.is_available():
        device = "cuda"
        print("Using GPU (CUDA)")
    elif torch.backends.mps.is_available():
        device = "mps"
        print("Using Apple Silicon GPU (MPS)")
    else:
        device = "cpu"
        print("Using CPU")

    # 2. Load Depth Anything V2 Model
    # We use 'Small-hf' for maximum real-time FPS.
    # (Swap to 'Depth-Anything-V2-Base-hf' if you have a powerful GPU and want higher precision)
    print("Loading Depth Anything V2 model...")
    model_id = "depth-anything/Depth-Anything-V2-Small-hf"
    image_processor = AutoImageProcessor.from_pretrained(model_id)
    model = AutoModelForDepthEstimation.from_pretrained(model_id).to(device).eval()

    # 3. Open the selected camera feed (Robeex by default)
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
        print("Error: Could not open camera stream.")
        return

    # 4. Initialize Open3D Visualizer Window
    vis = o3d.visualization.Visualizer()
    vis.create_window("Live 3D Map (Depth Anything V2)", width=1024, height=768)

    # Define camera intrinsics for 3D projection
    focal_length = max(width, height)
    intrinsic = o3d.camera.PinholeCameraIntrinsic(
        width, height, focal_length, focal_length, width / 2.0, height / 2.0
    )

    # Initialize empty point cloud
    pcd = o3d.geometry.PointCloud()
    is_pcd_added = False

    print(
        "Starting real-time 3D stream... Press 'q' in OpenCV window to stop."
    )

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Convert the OpenCV BGR frame to the RGB NumPy format expected by the model.
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 5. Run Depth Anything V2 Inference
        inputs = image_processor(images=rgb_frame, return_tensors="pt").to(device)
        with torch.inference_mode():
            predicted_depth = model(**inputs).predicted_depth

        # Extract depth map as a 2D float array
        raw_depth = predicted_depth.squeeze().float().cpu().numpy()

        # Ensure dimensions match camera frame
        if raw_depth.shape != (height, width):
            raw_depth = cv2.resize(
                raw_depth, (width, height), interpolation=cv2.INTER_LINEAR
            )

        # 6. Normalize and Convert Relative Depth to Pseudometric Distance
        # Depth Anything V2 outputs higher values for closer objects in relative scale.
        # We normalize to [0, 1] and invert so higher depth values = farther away in 3D.
        norm_depth = (raw_depth - raw_depth.min()) / (
            raw_depth.max() - raw_depth.min() + 1e-8
        )
        depth_in_meters = (1.0 - norm_depth) * 5.0 + 0.5  # Scale between 0.5m and 5.5m

        # 7. Generate RGB-D Pair & Create 3D Point Cloud
        o3d_color = o3d.geometry.Image(rgb_frame)
        o3d_depth = o3d.geometry.Image(depth_in_meters.astype(np.float32))

        rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
            o3d_color,
            o3d_depth,
            depth_scale=1.0,
            depth_trunc=6.0,  # Crop objects farther than 6 meters
            convert_rgb_to_intensity=False,
        )

        # Generate 3D geometry from RGB-D
        new_pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
            rgbd_image, intrinsic
        )

        # Voxel grid downsampling (Grid size = 3cm)
        # This aligns raw points into clean 3D voxels to reduce noise and increase FPS
        new_pcd = new_pcd.voxel_down_sample(voxel_size=0.03)

        # Flip coordinates so the scene renders right-side up
        new_pcd.transform(
            [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]
        )

        # 8. Render Update in Open3D
        pcd.points = new_pcd.points
        pcd.colors = new_pcd.colors

        if not is_pcd_added:
            vis.add_geometry(pcd)
            is_pcd_added = True
        else:
            vis.update_geometry(pcd)

        vis.poll_events()
        vis.update_renderer()

        # 9. Display 2D Camera Stream
        cv2.imshow("Live Feed (Depth Anything V2)", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Clean up
    cap.release()
    cv2.destroyAllWindows()
    vis.destroy_window()


if __name__ == "__main__":
    main()
