# RoBeeX AI Drone Python Examples

This repository contains small Python examples for controlling a RoBeeX drone, visualizing telemetry, and experimenting with computer vision and motion planning.

## Program overview

### Main demos
- [circle_cos_sin.py](circle_cos_sin.py) — Makes the drone fly a circular path while changing yaw based on sine and cosine values.
- [face_tracker.py](face_tracker.py) — Uses a camera stream and face detection to steer the drone toward a detected face.
- [motor_mixer_rgb_sim.py](motor_mixer_rgb_sim.py) — Simulates a motor mixer from drone roll/pitch telemetry and lights the LEDs accordingly.
- [mouse_control.py](mouse_control.py) — Maps drone tilt to mouse cursor movement with PyAutoGUI.
- [pitch_to_rgb.py](pitch_to_rgb.py) — Changes the drone RGB light color based on the current pitch value.
- [rgb_full_color_test.py](rgb_full_color_test.py) — Cycles the drone LEDs through different colors to test RGB output.

### Flight path examples
- [flight_path/generate_circle_path.py](flight_path/generate_circle_path.py) — Generates a pickle file containing a circular flight path.
- [flight_path/fly_with_generated_path.py](flight_path/fly_with_generated_path.py) — Loads a generated path and sends the drone through the saved waypoints.
- [flight_path/generate_text_cords.py](flight_path/generate_text_cords.py) — Extracts outline coordinates from a font to create text-based flight paths.

### AprilTag / ArUco examples
- [april_tag/april_tag_gen.py](april_tag/april_tag_gen.py) — Generates an ArUco/AprilTag image for a chosen ID and tag family.
- [april_tag/april_tag_detect.py](april_tag/april_tag_detect.py) — Detects tags in an image and visualizes their estimated pose in 3D.
- [april_tag/app_aruco_detector.py](april_tag/app_aruco_detector.py) — A reusable detector class for finding ArUco tags and estimating their position/orientation.
- [april_tag/april_tag_3d.py](april_tag/april_tag_3d.py) — Runs a real-time tag detector and publishes pose data over WebSockets.
- [april_tag/calibration.py](april_tag/calibration.py) — Helps calibrate a camera using a chessboard pattern.
- [april_tag/ws_server.py](april_tag/ws_server.py) — Starts a simple WebSocket server for broadcasting messages.
- [april_tag/test_ws.py](april_tag/test_ws.py) — Sends sample telemetry over the WebSocket server for testing.
