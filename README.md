# RoBeeX AI Drone Python Examples

**Languages:** English | [فارسی](README.fa.md) | [العربية](README.ar.md)

Examples for controlling the RoBeeX AI Drone, viewing its camera and telemetry,
generating flight paths, and running computer-vision models on live video.

**Official resources:** [RoBeeX website](https://robeex.com/) |
[English documentation](https://docs.robeex.com/en/)

> [!CAUTION]
> Flight examples can arm, take off, move, and land a real drone. Use a clear
> test area and keep emergency disarm available. Preview generated paths before
> enabling flight.

## Setup

Python 3.11+ is required. From the repository root:

```bash
uv sync
```

Commands below use `uv run python`. Most drone examples wait for telemetry, so
the computer must be connected to the drone. Video and 3D programs need a
graphical desktop.

`pyproject.toml` declares the RoBeeX AI Drone API, NumPy, OpenCV, PyAutoGUI, CVZone, and
MediaPipe. Advanced examples also use packages that are not currently declared:

```bash
uv pip install ultralytics torch open3d transformers pyvista freetype-py websocket-server
```

- Ultralytics/Torch run YOLO26; Open3D renders point clouds and voxels.
- Transformers downloads and runs Depth Anything V2 from Hugging Face.
- PyVista renders AprilTag pose, FreeType reads font outlines, and
  `websocket-server` publishes telemetry/tag JSON.

YOLO scripts expect the included `.pt` files in the repository root. Depth
Anything downloads `depth-anything/Depth-Anything-V2-Small-hf` on first use.
The two object detection scripts explicitly require CUDA; depth scripts select
CUDA, Apple MPS, or CPU automatically.

## Camera and general examples

### Camera stream

```bash
uv run python others/camera_stream.py [-f FRAME_SIZE] [-q JPEG_QUALITY] [--blur]
```

[camera_stream.py](others/camera_stream.py) opens the RoBeeX UDP/JPEG stream via
`robeex-ai-drone-api`, displays it with OpenCV, and reports failed frames as
packet loss each second. Press `q` to exit.

- `-f`, `--frame_size`: default `7` (`480x320`). API values are `4` (`240x240`),
  `5` (`320x240`), `6` (`400x296`), `7` (`480x320`), `8` (`640x480`), `9`
  (`800x600`), `10` (`1024x768`), `11` (`HD`), and `12` (`XHD`). The parser also
  accepts `13`, but the API rejects it.
- `-q`, `--jpeg_quality`: `1`–`63`, default `15`; lower means more compression.
- `--blur`: apply OpenCV median and Gaussian blur.

### Face tracker

```bash
uv run python others/face_tracker.py
```

[face_tracker.py](others/face_tracker.py) uses CVZone `FaceDetector` (MediaPipe's
short-range face detector) on a `640x480` RoBeeX stream. A proportional controller
adjusts altitude and yaw toward the first face. LEDs show red when a face is found
and green otherwise. It has no flags. Keys: `1` arm/take off to 1.1 m, `l` land,
`0` disarm, `q` exit.

### Mouse control

```bash
uv run python others/mouse_control.py
```

[mouse_control.py](others/mouse_control.py) maps drone pitch/yaw to screen
coordinates with PyAutoGUI. A 2-degree dead zone suppresses motion near level, and
exponential interpolation smooths pointer movement. Roll at least 30 degrees left
for a left click or right for a right click; return within 20 degrees of level before
the next click. Rotating yaw 180 degrees from its starting orientation stops the
program. It has no flags.

## RGB LED examples

```bash
uv run python rgb/rgb_full_color_test.py
uv run python rgb/pitch_to_rgb.py
uv run python rgb/motor_mixer_rgb_sim.py
```

These have no flags and use RoBeeX telemetry/RGB commands:

- [rgb_full_color_test.py](rgb/rgb_full_color_test.py) converts rotating OpenCV
  HSV hues to RGB and phase-shifts the color across four motor LEDs.
- [pitch_to_rgb.py](rgb/pitch_to_rgb.py) maps positive pitch from green to red.
- [motor_mixer_rgb_sim.py](rgb/motor_mixer_rgb_sim.py) turns roll/pitch into four
  simulated mixer outputs and maps them to the corresponding motor LEDs.

Stop continuous examples with `Ctrl+C`.

## Object detection and segmentation

```bash
uv run python object_detection/yolo_object_detection.py [-c]
uv run python object_detection/yolo_object_segmentation.py [-c]
```

- [yolo_object_detection.py](object_detection/yolo_object_detection.py) uses
  Ultralytics `YOLO` with `yolo26l.pt`, CUDA, and confidence `0.45` to draw boxes.
- [yolo_object_segmentation.py](object_detection/yolo_object_segmentation.py) uses
  `yolo26l-seg.pt` with the same settings to draw instance masks.
- `-c`, `--cam`: use webcam `0`; otherwise use RoBeeX HD/JPEG quality `16`.

Press `q` to exit.

## Depth estimation and 3D mapping

All programs default to RoBeeX `640x480`, JPEG quality `16`. `-c`/`--cam` selects
webcam `0`; press `q` in the OpenCV window to exit.

```bash
uv run python depth_estimation/yolo_depth.py [-c]
uv run python depth_estimation/yolo_depth_point_cloud_3d.py [-c]
uv run python depth_estimation/yolo_depth_voxal_3d.py [-c]
uv run python depth_estimation/depth_any_thing.py [-c]
```

- [yolo_depth.py](depth_estimation/yolo_depth.py) runs Ultralytics
  `yolo26n-depth.pt` and shows raw/colored depth, FPS, and center distance.
- [yolo_depth_point_cloud_3d.py](depth_estimation/yolo_depth_point_cloud_3d.py)
  runs `yolo26l-depth.pt`, combines metric depth with RGB, and projects an Open3D
  point cloud using approximate pinhole intrinsics.
- [yolo_depth_voxal_3d.py](depth_estimation/yolo_depth_voxal_3d.py) runs
  `yolo26l-depth.pt` and converts each RGB-D cloud to 1 cm Open3D voxels. The
  filename retains the repository's existing `voxal` spelling.
- [depth_any_thing.py](depth_estimation/depth_any_thing.py) runs Transformers
  `Depth-Anything-V2-Small-hf`, maps relative depth to a visual pseudo-range of
  0.5–5.5 m, and creates a 3 cm-downsampled Open3D cloud. It is not calibrated
  metric depth.

## Flight paths

### Direct circle

```bash
uv run python flight_path/circle_cos_sin.py
```

[circle_cos_sin.py](flight_path/circle_cos_sin.py) has no flags. It arms, takes
off to 1 m, sends cosine/sine XY targets around a 1 m-radius circle while changing
yaw, returns to the origin, lands, and disarms.

### Generate, preview, and fly a path

Relative output paths require running generators inside `flight_path/`:

```bash
cd flight_path
uv run python generate_circle_path.py
cd ..
```

[generate_circle_path.py](flight_path/generate_circle_path.py) has no flags. It
samples a half-meter-radius circle every 0.1 radian and writes
`flight_path/circle_coordinates.pkl`.

```bash
uv run python flight_path/fly_with_generated_path.py flight_path/circle_coordinates.pkl
uv run python flight_path/fly_with_generated_path.py flight_path/circle_coordinates.pkl --flight
```

[fly_with_generated_path.py](flight_path/fly_with_generated_path.py) renders a
pickled sequence of `(x, y)` meter coordinates. With flight enabled it sends each
as drone `(x, 0, y + 0.5)`.

- `pickle_path`: required pickle path.
- `--flight` / `--no-flight`: enable/disable real movement; default disabled.
  When enabled, type `y`, press `a` to arm, then `t` to take off. During traversal,
  `0` disarms and `q` stops; press `q` again at the final window.

### Text path

```bash
cd flight_path
uv run python generate_text_cords.py
cd ..
```

[generate_text_cords.py](flight_path/generate_text_cords.py) uses FreeType to
decompose the bundled JetBrains Mono Nerd Font outline for hard-coded character
`S`, samples line/quadratic curves, normalizes them to 0.75 units, and writes
`text-cords.pkl`. It has no flags; font, character, and precision are source values.

## AprilTag / ArUco examples

These use OpenCV `cv2.aruco`. Run detection from `april_tag/` because calibration
paths are relative. Pose estimation assumes a physical tag side of 0.1 m.

### Generate a marker

```bash
cd april_tag
uv run python april_tag_gen.py -o tag.png -i 7 [-t DICTIONARY] [-p PIXELS]
cd ..
```

[april_tag_gen.py](april_tag/april_tag_gen.py) generates a 300x300 marker, pads,
saves, and displays it using OpenCV.

- `-o`, `--output`: required image path.
- `-i`, `--id`: required marker ID valid for the dictionary.
- `-t`, `--type`: default `DICT_ARUCO_ORIGINAL`. Supports OpenCV `DICT_4X4_*`,
  `DICT_5X5_*`, `DICT_6X6_*`, `DICT_7X7_*`, `DICT_ARUCO_ORIGINAL`, and AprilTag
  `16h5`, `25h9`, `36h10`, and `36h11` dictionary names.
- `-p`, `--padding`: white-border pixels, default `50`; `0` disables it.

### Detect and visualize pose

```bash
cd april_tag
uv run python april_tag_detect.py [-c CAMERA] [-t DICTIONARY]
cd ..
```

[april_tag_detect.py](april_tag/april_tag_detect.py) detects markers, uses OpenCV
`solvePnP` and stored camera calibration for translation/rotation, and displays
pose with OpenCV and PyVista.

- `-c`, `--cam`: `robeex` (default) or numeric webcam index such as `0`; selects
  `calibration_data_robeex.npz` or `calibration_data_pc.npz`.
- `-t`, `--type`: dictionary name, default `DICT_5X5_100`.

It currently waits for RoBeeX telemetry even with a local camera. Press `q` to exit.

### Publish pose over WebSockets

```bash
cd april_tag
uv run python april_tag_3d.py [-c CAMERA] [-t DICTIONARY] [--multi-tag]
cd ..
```

[april_tag_3d.py](april_tag/april_tag_3d.py) uses
[app_aruco_detector.py](april_tag/app_aruco_detector.py) for `solvePnP` pose and
[ws_server.py](april_tag/ws_server.py) to broadcast telemetry at
`ws://127.0.0.1:8686` and tag JSON at `ws://127.0.0.1:8687`.

- `-c`, `--cam`: `robeex` (default) or numeric webcam index.
- `-t`, `--type`: dictionary, default `DICT_5X5_100`.
- `-mt`, `--multi-tag` / `--no-multi-tag`: publish all tags rather than the first;
  default off. Prefer the long form due to `argparse` BooleanOptionalAction naming.

Press `.` to exit with RoBeeX camera or `q` with a local camera.

### Calibration preview and WebSocket helpers

```bash
uv run python april_tag/calibration.py
```

[calibration.py](april_tag/calibration.py) opens webcam `0` and overlays detection
for a hard-coded 7x6-inner-corner chessboard. It only previews detection; it does
not calculate or save calibration. Press `q` to exit.

[ws_server.py](april_tag/ws_server.py) defines `BroadcastServer`, and
[test_ws.py](april_tag/test_ws.py) is intended to publish sample telemetry. Their
standalone blocks currently omit the required `port`, so running either directly
raises `TypeError`; they are documented as helpers, not runnable commands.

## Contributing

Contributions and fixes are welcome through issues or pull requests.
