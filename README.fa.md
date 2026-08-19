# نمونه‌های Python برای RoBeeX AI Drone

**زبان‌ها:** [English](README.md) | فارسی | [العربية](README.ar.md)

این مخزن شامل نمونه‌هایی برای کنترل محصول RoBeeX AI Drone، مشاهده‌ی دوربین و telemetry،
ساخت مسیر پرواز و اجرای مدل‌های computer vision روی ویدیوی زنده است.

**منابع رسمی:** [وب‌سایت فارسی RoBeeX](https://robeex.ir/) |
[مستندات فارسی](https://docs.robeex.com/fa/)

> [!CAUTION]
> نمونه‌های پرواز می‌توانند پهپاد واقعی را arm کنند، به پرواز درآورند، حرکت دهند
> و فرود بیاورند. آزمایش را در محیطی کنترل‌شده و بدون مانع انجام دهید، امکان emergency
> disarm را در دسترس نگه دارید و پیش از فعال‌کردن پرواز، مسیرهای تولیدشده را preview کنید.

## راه‌اندازی

Python 3.11 یا جدیدتر لازم است. در ریشه‌ی repository اجرا کنید:

```bash
uv sync
```

دستورهای این سند از `uv run python` استفاده می‌کنند. بیشتر نمونه‌های پهپاد منتظر
telemetry می‌مانند؛ بنابراین کامپیوتر باید به پهپاد متصل باشد. برنامه‌های ویدیو و
نمایش سه‌بعدی نیز به محیط desktop گرافیکی نیاز دارند.

وابستگی‌های اصلی در `pyproject.toml` تعریف شده‌اند. نمونه‌های پیشرفته به packageهای
زیر هم نیاز دارند که در حال حاضر در آن فایل تعریف نشده‌اند:

```bash
uv pip install ultralytics torch open3d transformers pyvista freetype-py websocket-server
```

- Ultralytics و Torch مدل‌های YOLO26 را اجرا می‌کنند؛ Open3D برای point cloud و voxel است.
- Transformers مدل Depth Anything V2 را از Hugging Face دریافت و اجرا می‌کند.
- PyVista نمایش pose مربوط به AprilTag، FreeType خواندن outline فونت و
  `websocket-server` انتشار telemetry و JSON تگ را انجام می‌دهند.

اسکریپت‌های YOLO فایل‌های `.pt` موجود در ریشه‌ی repository را می‌خوانند. Depth
Anything در اولین اجرا مدل `depth-anything/Depth-Anything-V2-Small-hf` را دانلود
می‌کند. دو اسکریپت object detection در وضعیت فعلی صراحتاً به CUDA نیاز دارند؛
اسکریپت‌های depth به‌صورت خودکار CUDA، Apple MPS یا CPU را انتخاب می‌کنند.

## دوربین و نمونه‌های عمومی

### نمایش stream دوربین

```bash
uv run python others/camera_stream.py [-f FRAME_SIZE] [-q JPEG_QUALITY] [--blur]
```

[camera_stream.py](others/camera_stream.py) با `robeex-ai-drone-api`، stream مبتنی
بر UDP/JPEG پهپاد را باز می‌کند، تصویر را با OpenCV نمایش می‌دهد و هر ثانیه frameهای
ناموفق را به‌عنوان packet loss گزارش می‌کند. برای خروج `q` را بزنید.

- `-f`، `--frame_size`: مقدار پیش‌فرض `7` (`480x320`). مقادیر API عبارت‌اند از
  `4` (`240x240`)، `5` (`320x240`)، `6` (`400x296`)، `7` (`480x320`)، `8`
  (`640x480`)، `9` (`800x600`)، `10` (`1024x768`)، `11` (`HD`) و `12` (`XHD`).
  parser مقدار `13` را هم می‌پذیرد، اما API آن را رد می‌کند.
- `-q`، `--jpeg_quality`: عدد `1` تا `63`، با مقدار پیش‌فرض `15`؛ عدد کمتر یعنی compression بیشتر.
- `--blur`: اعمال median blur و Gaussian blur در OpenCV.

### دنبال‌کردن چهره

```bash
uv run python others/face_tracker.py
```

[face_tracker.py](others/face_tracker.py) از `FaceDetector` در CVZone، مبتنی بر
مدل short-range در MediaPipe، روی stream با ابعاد `640x480` استفاده می‌کند. یک
proportional controller ارتفاع و yaw را برای قرار دادن اولین چهره در مرکز تنظیم
می‌کند. LED هنگام تشخیص چهره قرمز و در غیر این صورت سبز است. این برنامه flag ندارد.
کلیدها: `1` برای arm و takeoff تا ارتفاع 1.1 متر، `l` برای land، `0` برای disarm و `q` برای خروج.

### کنترل ماوس

```bash
uv run python others/mouse_control.py
```

[mouse_control.py](others/mouse_control.py) با PyAutoGUI مقادیر pitch و yaw پهپاد را
به مختصات صفحه نگاشت می‌کند. یک ناحیهٔ بی‌اثر ۲ درجه‌ای حرکت نزدیک حالت تراز را
حذف می‌کند و درون‌یابی نمایی حرکت نشانگر را نرم‌تر می‌کند. roll حداقل ۳۰ درجه به
چپ، کلیک چپ و به راست، کلیک راست انجام می‌دهد؛ برای کلیک بعدی پهپاد را به محدودهٔ
۲۰ درجه از حالت تراز برگردانید. چرخاندن yaw به اندازهٔ ۱۸۰ درجه نسبت به جهت شروع،
برنامه را متوقف می‌کند. این برنامه flag ندارد.

## نمونه‌های RGB LED

```bash
uv run python rgb/rgb_full_color_test.py
uv run python rgb/pitch_to_rgb.py
uv run python rgb/motor_mixer_rgb_sim.py
```

این اسکریپت‌ها flag ندارند و از telemetry و فرمان‌های RGB در RoBeeX استفاده می‌کنند:

- [rgb_full_color_test.py](rgb/rgb_full_color_test.py) رنگ HSV چرخان را با OpenCV
  به RGB تبدیل می‌کند و رنگ را با اختلاف فاز روی چهار LED موتور اعمال می‌کند.
- [pitch_to_rgb.py](rgb/pitch_to_rgb.py) pitch مثبت را از سبز به قرمز نگاشت می‌کند.
- [motor_mixer_rgb_sim.py](rgb/motor_mixer_rgb_sim.py) roll و pitch را به چهار خروجی
  شبیه‌سازی‌شده‌ی mixer تبدیل و روی LED موتور متناظر اعمال می‌کند.

برای توقف نمونه‌های پیوسته `Ctrl+C` را بزنید.

## Object detection و segmentation

```bash
uv run python object_detection/yolo_object_detection.py [-c]
uv run python object_detection/yolo_object_segmentation.py [-c]
```

- [yolo_object_detection.py](object_detection/yolo_object_detection.py) با API
  کلاس `YOLO` در Ultralytics، وزن `yolo26l.pt`، CUDA و confidence برابر `0.45`
  bounding boxها را رسم می‌کند.
- [yolo_object_segmentation.py](object_detection/yolo_object_segmentation.py) با
  وزن `yolo26l-seg.pt` و همان تنظیمات، instance maskها را رسم می‌کند.
- `-c`، `--cam`: استفاده از webcam شماره‌ی `0`؛ بدون آن، stream پهپاد با کیفیت
  `HD` و JPEG quality برابر `16` استفاده می‌شود.

برای خروج `q` را بزنید.

## تخمین عمق و نگاشت سه‌بعدی

همه‌ی برنامه‌ها به‌صورت پیش‌فرض از stream پهپاد با ابعاد `640x480` و JPEG quality
برابر `16` استفاده می‌کنند. `-c` یا `--cam`، webcam شماره‌ی `0` را انتخاب می‌کند.

```bash
uv run python depth_estimation/yolo_depth.py [-c]
uv run python depth_estimation/yolo_depth_point_cloud_3d.py [-c]
uv run python depth_estimation/yolo_depth_voxal_3d.py [-c]
uv run python depth_estimation/depth_any_thing.py [-c]
```

- [yolo_depth.py](depth_estimation/yolo_depth.py) مدل `yolo26n-depth.pt` را اجرا و
  depth خام و رنگی، FPS و فاصله‌ی pixel مرکزی را نمایش می‌دهد.
- [yolo_depth_point_cloud_3d.py](depth_estimation/yolo_depth_point_cloud_3d.py)
  با `yolo26l-depth.pt`، depth متریک را با RGB ترکیب می‌کند و با camera intrinsics
  تقریبی یک point cloud در Open3D می‌سازد.
- [yolo_depth_voxal_3d.py](depth_estimation/yolo_depth_voxal_3d.py) همان مدل را
  اجرا و هر RGB-D cloud را به voxelهای 1 سانتی‌متری تبدیل می‌کند. نام فایل با املای
  فعلی `voxal` حفظ شده است.
- [depth_any_thing.py](depth_estimation/depth_any_thing.py) مدل
  `Depth-Anything-V2-Small-hf` را اجرا، relative depth را به بازه‌ی نمایشی 0.5 تا
  5.5 متر نگاشت و point cloud را با voxel 3 سانتی‌متری downsample می‌کند. این خروجی
  depth متریک کالیبره‌شده نیست.

برای خروج، در پنجره‌ی OpenCV کلید `q` را بزنید.

## مسیرهای پرواز

### پرواز مستقیم روی دایره

```bash
uv run python flight_path/circle_cos_sin.py
```

[circle_cos_sin.py](flight_path/circle_cos_sin.py) flag ندارد. پهپاد را arm می‌کند،
تا ارتفاع 1 متر takeoff می‌کند، targetهای XY حاصل از cosine/sine را روی دایره‌ای
با شعاع 1 متر همراه با تغییر yaw می‌فرستد، به مبدأ برمی‌گردد، land و سپس disarm می‌کند.

### تولید، preview و اجرای مسیر

به‌دلیل relative بودن مسیر خروجی، generatorها را داخل `flight_path/` اجرا کنید:

```bash
cd flight_path
uv run python generate_circle_path.py
cd ..
```

[generate_circle_path.py](flight_path/generate_circle_path.py) flag ندارد، دایره‌ای
با شعاع 0.5 متر را با گام 0.1 رادیان sample می‌کند و در
`flight_path/circle_coordinates.pkl` می‌نویسد.

```bash
uv run python flight_path/fly_with_generated_path.py flight_path/circle_coordinates.pkl
uv run python flight_path/fly_with_generated_path.py flight_path/circle_coordinates.pkl --flight
```

[fly_with_generated_path.py](flight_path/fly_with_generated_path.py) دنباله‌ی
pickleشده‌ی مختصات متری `(x, y)` را نمایش می‌دهد و در حالت پرواز هر نقطه را به شکل
`(x, 0, y + 0.5)` برای پهپاد می‌فرستد.

- `pickle_path`: مسیر الزامی فایل pickle.
- `--flight` / `--no-flight`: فعال یا غیرفعال‌کردن حرکت واقعی؛ پیش‌فرض غیرفعال است.
  برای پرواز `y` را وارد کنید، `a` را برای arm و سپس `t` را برای takeoff بزنید.
  هنگام اجرا `0` disarm و `q` مسیر را متوقف می‌کند؛ در پنجره‌ی نهایی دوباره `q` را بزنید.

### مسیر متنی

```bash
cd flight_path
uv run python generate_text_cords.py
cd ..
```

[generate_text_cords.py](flight_path/generate_text_cords.py) با FreeType، outline
کاراکتر hard-coded شده‌ی `S` را از فونت JetBrains Mono Nerd Font استخراج، curveها
را sample و به 0.75 واحد normalize می‌کند و در `text-cords.pkl` می‌نویسد. flag ندارد؛
فونت، کاراکتر و precision باید در source تغییر کنند.

## نمونه‌های AprilTag / ArUco

این نمونه‌ها از `cv2.aruco` استفاده می‌کنند. چون مسیر calibration نسبی است، برنامه‌های
detection را از داخل `april_tag/` اجرا کنید. pose estimation طول ضلع فیزیکی تگ را
0.1 متر فرض می‌کند.

### تولید marker

```bash
cd april_tag
uv run python april_tag_gen.py -o tag.png -i 7 [-t DICTIONARY] [-p PIXELS]
cd ..
```

- `-o`، `--output`: مسیر الزامی تصویر خروجی.
- `-i`، `--id`: شناسه‌ی الزامی و معتبر در dictionary انتخابی.
- `-t`، `--type`: پیش‌فرض `DICT_ARUCO_ORIGINAL`. خانواده‌های `DICT_4X4_*` تا
  `DICT_7X7_*`، `DICT_ARUCO_ORIGINAL` و AprilTagهای `16h5`، `25h9`، `36h10` و
  `36h11` پشتیبانی می‌شوند.
- `-p`، `--padding`: حاشیه‌ی سفید برحسب pixel، پیش‌فرض `50`؛ مقدار `0` آن را حذف می‌کند.

[april_tag_gen.py](april_tag/april_tag_gen.py) با OpenCV یک marker با ابعاد
300x300 می‌سازد، حاشیه اضافه می‌کند، آن را ذخیره و نمایش می‌دهد.

### تشخیص و نمایش pose

```bash
cd april_tag
uv run python april_tag_detect.py [-c CAMERA] [-t DICTIONARY]
cd ..
```

[april_tag_detect.py](april_tag/april_tag_detect.py) markerها را تشخیص می‌دهد، با
OpenCV `solvePnP` و calibration ذخیره‌شده translation/rotation را محاسبه می‌کند و
pose را با OpenCV و PyVista نمایش می‌دهد.

- `-c`، `--cam`: مقدار `robeex` (پیش‌فرض) یا index عددی webcam مانند `0`؛ به‌ترتیب
  فایل `calibration_data_robeex.npz` یا `calibration_data_pc.npz` انتخاب می‌شود.
- `-t`، `--type`: نام dictionary، پیش‌فرض `DICT_5X5_100`.

در وضعیت فعلی حتی با دوربین محلی نیز منتظر telemetry پهپاد می‌ماند. خروج با `q`.

### انتشار pose با WebSocket

```bash
cd april_tag
uv run python april_tag_3d.py [-c CAMERA] [-t DICTIONARY] [--multi-tag]
cd ..
```

[april_tag_3d.py](april_tag/april_tag_3d.py) از
[app_aruco_detector.py](april_tag/app_aruco_detector.py) برای pose و از
[ws_server.py](april_tag/ws_server.py) برای انتشار telemetry روی
`ws://127.0.0.1:8686` و JSON تگ روی `ws://127.0.0.1:8687` استفاده می‌کند.

- `-c`، `--cam`: `robeex` یا index عددی webcam.
- `-t`، `--type`: dictionary، پیش‌فرض `DICT_5X5_100`.
- `-mt`، `--multi-tag` / `--no-multi-tag`: انتشار همه‌ی تگ‌ها به‌جای اولین تگ؛
  پیش‌فرض خاموش است. به‌دلیل نام‌گذاری `BooleanOptionalAction`، long form مناسب‌تر است.

با دوربین RoBeeX کلید `.` و با دوربین محلی `q` برنامه را می‌بندد.

### preview کالیبراسیون و helperهای WebSocket

```bash
uv run python april_tag/calibration.py
```

[calibration.py](april_tag/calibration.py) webcam شماره‌ی `0` را باز و تشخیص
chessboard با 7x6 گوشه‌ی داخلی را overlay می‌کند. این برنامه فقط preview است و
calibration را محاسبه یا ذخیره نمی‌کند. خروج با `q`.

[ws_server.py](april_tag/ws_server.py) کلاس `BroadcastServer` را تعریف می‌کند و
[test_ws.py](april_tag/test_ws.py) برای انتشار telemetry نمونه در نظر گرفته شده است.
بلوک standalone هر دو فایل آرگومان الزامی `port` را ارسال نمی‌کند؛ بنابراین اجرای
مستقیم آن‌ها `TypeError` می‌دهد و باید آن‌ها را helper در نظر گرفت.

## مشارکت

Issueها، pull requestها و اصلاحات شما پذیرفته می‌شوند.
