# أمثلة Python لـ RoBeeX AI Drone

**اللغات:** [English](README.md) | [فارسی](README.fa.md) | العربية

يحتوي هذا المستودع على أمثلة للتحكم في RoBeeX AI Drone، وعرض الكاميرا وبيانات
telemetry، وإنشاء مسارات الطيران، وتشغيل نماذج computer vision على بث حي.

**المصادر الرسمية:** [موقع RoBeeX](https://robeex.com/) |
[التوثيق باللغة الإنجليزية](https://docs.robeex.com/en/)

> [!CAUTION]
> تستطيع أمثلة الطيران تنفيذ arm والإقلاع وتحريك طائرة حقيقية ثم الهبوط. اختبرها
> في مكان خالٍ من العوائق، وأبقِ emergency disarm في متناولك، واعرض أي مسار مُنشأ
> قبل تفعيل الطيران الفعلي.

## الإعداد

يتطلب المشروع Python 3.11 أو أحدث. اختر `uv` أو `pip` ونفّذ من جذر repository.

باستخدام `uv`:

```bash
uv sync
```

باستخدام `pip`:

```bash
pip install -r requirements.txt
```

باستخدام `pip` مع *virtual environment*:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
```

تستخدم الأوامر أدناه `uv run python`. إذا ثبّتَّ الحزم باستخدام `pip`، فاستبدل
`uv run python` بـ `python`. تنتظر معظم أمثلة الطائرة وصول telemetry، لذلك يجب
أن يكون الحاسوب متصلاً بالطائرة. وتتطلب تطبيقات الفيديو والعرض ثلاثي الأبعاد بيئة
desktop رسومية.

يعرّف `pyproject.toml` الاعتماديات الأساسية. تحتاج الأمثلة المتقدمة أيضاً إلى
الحزم التالية، وهي غير معرّفة فيه حالياً:

باستخدام `uv`:

```bash
uv pip install ultralytics torch open3d transformers pyvista freetype-py websocket-server
```

باستخدام `pip`:

```bash
python -m pip install ultralytics torch open3d transformers pyvista freetype-py websocket-server
```

- يشغّل Ultralytics وTorch نماذج YOLO26، ويعرض Open3D الـ point cloud والـ voxels.
- يحمّل Transformers نموذج Depth Anything V2 من Hugging Face ويشغّله.
- يُستخدم PyVista لعرض pose الخاص بـ AprilTag، وFreeType لقراءة font outlines،
  و`websocket-server` لنشر telemetry وبيانات التاغ بصيغة JSON.

ملفات أوزان YOLO ذات الامتداد `.pt` غير مضمّنة في repository. يحمّل Ultralytics
النموذج المطلوب تلقائياً عند تشغيل كل سكربت YOLO للمرة الأولى، لذلك يلزم اتصال
بالإنترنت عند أول استخدام. يحمّل Depth Anything أيضاً النموذج
`depth-anything/Depth-Anything-V2-Small-hf` عند أول تشغيل. يتطلب سكربتا object
detection حالياً CUDA بشكل صريح، بينما تختار سكربتات depth تلقائياً بين CUDA
وApple MPS وCPU.

## الكاميرا والأمثلة العامة

### عرض بث الكاميرا

```bash
uv run python others/camera_stream.py [-f FRAME_SIZE] [-q JPEG_QUALITY] [--blur]
```

يفتح [camera_stream.py](others/camera_stream.py) بث RoBeeX المعتمد على UDP/JPEG
عبر `robeex-ai-drone-api`، ويعرضه باستخدام OpenCV، ويحسب الـ frames الفاشلة كـ
packet loss مرة كل ثانية. اضغط `q` للخروج.

- `-f`، `--frame_size`: القيمة الافتراضية `7` (`480x320`). قيم API هي `4`
  (`240x240`)، و`5` (`320x240`)، و`6` (`400x296`)، و`7` (`480x320`)، و`8`
  (`640x480`)، و`9` (`800x600`)، و`10` (`1024x768`)، و`11` (`HD`)، و`12`
  (`XHD`). يقبل parser القيمة `13` أيضاً، لكن API يرفضها.
- `-q`، `--jpeg_quality`: عدد من `1` إلى `63`، والقيمة الافتراضية `15`؛ الرقم
  الأصغر يعني compression أعلى.
- `--blur`: تطبيق median blur وGaussian blur من OpenCV.

### تتبّع الوجه

```bash
uv run python others/face_tracker.py
```

يستخدم [face_tracker.py](others/face_tracker.py) الكلاس `FaceDetector` من CVZone،
والمبني على short-range face detector في MediaPipe، على بث RoBeeX بدقة `640x480`.
يضبط proportional controller الارتفاع وyaw لتوسيط أول وجه. تضيء LED بالأحمر عند
وجود وجه وبالأخضر في غير ذلك. لا توجد flags. المفاتيح: `1` لتنفيذ arm والإقلاع
إلى 1.1 متر، و`l` للهبوط، و`0` لتنفيذ disarm، و`q` للخروج.

### التحكم بالماوس

```bash
uv run python others/mouse_control.py
```

يحوّل [mouse_control.py](others/mouse_control.py) قيمتي pitch وyaw إلى إحداثيات
الشاشة عبر PyAutoGUI. تمنع منطقة خمول بمقدار درجتين الحركة قرب وضع الاستواء، ويجعل
الاستيفاء الأُسّي حركة المؤشر أكثر سلاسة. نفّذ roll بمقدار 30 درجة على الأقل إلى
اليسار للنقر بالزر الأيسر أو إلى اليمين للنقر بالزر الأيمن، ثم أعده إلى نطاق 20
درجة من الاستواء قبل النقرة التالية. يؤدي تدوير yaw بمقدار 180 درجة من اتجاه
البداية إلى إيقاف البرنامج. لا توجد flags.

## أمثلة RGB LED

```bash
uv run python rgb/rgb_full_color_test.py
uv run python rgb/pitch_to_rgb.py
uv run python rgb/motor_mixer_rgb_sim.py
```

لا تملك هذه السكربتات flags، وتستخدم telemetry وأوامر RGB في RoBeeX:

- يحوّل [rgb_full_color_test.py](rgb/rgb_full_color_test.py) درجات HSV المتغيرة
  إلى RGB باستخدام OpenCV، ثم يزيح اللون طورياً بين مصابيح المحركات الأربعة.
- يحوّل [pitch_to_rgb.py](rgb/pitch_to_rgb.py) قيمة pitch الموجبة من الأخضر إلى الأحمر.
- يحوّل [motor_mixer_rgb_sim.py](rgb/motor_mixer_rgb_sim.py) قيمتي roll وpitch إلى
  أربعة مخارج mixer محاكية، ثم يطبقها على LED كل محرك.

أوقف الأمثلة المستمرة باستخدام `Ctrl+C`.

## Object detection وsegmentation

```bash
uv run python object_detection/yolo_object_detection.py [-c]
uv run python object_detection/yolo_object_segmentation.py [-c]
```

- يستخدم [yolo_object_detection.py](object_detection/yolo_object_detection.py)
  API الكلاس `YOLO` من Ultralytics مع `yolo26l.pt` وCUDA وconfidence بقيمة `0.45`
  لرسم bounding boxes.
- يستخدم [yolo_object_segmentation.py](object_detection/yolo_object_segmentation.py)
  الملف `yolo26l-seg.pt` بالإعدادات نفسها لرسم instance masks.
- `-c`، `--cam`: استخدام webcam رقم `0`؛ ومن دونه يُستخدم بث RoBeeX بدقة `HD`
  وJPEG quality بقيمة `16`.

اضغط `q` للخروج.

## تقدير العمق وبناء المشهد ثلاثي الأبعاد

تستخدم البرامج الأربعة افتراضياً بث RoBeeX بدقة `640x480` وJPEG quality بقيمة
`16`. يختار `-c` أو `--cam` الـ webcam رقم `0`.

```bash
uv run python depth_estimation/yolo_depth.py [-c]
uv run python depth_estimation/yolo_depth_point_cloud_3d.py [-c]
uv run python depth_estimation/yolo_depth_voxal_3d.py [-c]
uv run python depth_estimation/depth_any_thing.py [-c]
```

- يشغّل [yolo_depth.py](depth_estimation/yolo_depth.py) نموذج
  `yolo26n-depth.pt`، ويعرض depth الخام والملوّن وFPS ومسافة الـ pixel المركزي.
- يشغّل [yolo_depth_point_cloud_3d.py](depth_estimation/yolo_depth_point_cloud_3d.py)
  نموذج `yolo26l-depth.pt`، ويدمج metric depth مع RGB، ثم يبني point cloud في
  Open3D باستخدام camera intrinsics تقريبية.
- يشغّل [yolo_depth_voxal_3d.py](depth_estimation/yolo_depth_voxal_3d.py) النموذج
  نفسه ويحوّل كل RGB-D cloud إلى voxels بحجم 1 سم. احتُفظ بالتهجئة الحالية `voxal`
  في اسم الملف.
- يشغّل [depth_any_thing.py](depth_estimation/depth_any_thing.py) نموذج
  `Depth-Anything-V2-Small-hf`، ويحوّل relative depth إلى نطاق بصري من 0.5 إلى
  5.5 متر، ثم يعمل downsample للـ point cloud بحجم 3 سم. الناتج ليس metric depth
  مُعايراً.

اضغط `q` داخل نافذة OpenCV للخروج.

## مسارات الطيران

### طيران دائري مباشر

```bash
uv run python flight_path/circle_cos_sin.py
```

لا يملك [circle_cos_sin.py](flight_path/circle_cos_sin.py) flags. ينفّذ arm،
ويقلع إلى ارتفاع متر، ويرسل أهداف XY محسوبة بـ cosine/sine على دائرة نصف قطرها
متر مع تغيير yaw، ثم يعود إلى نقطة الأصل ويهبط وينفّذ disarm.

### إنشاء المسار ومعاينته وتنفيذه

بسبب استخدام مسارات إخراج نسبية، شغّل الـ generators من داخل `flight_path/`:

```bash
cd flight_path
uv run python generate_circle_path.py
cd ..
```

لا يملك [generate_circle_path.py](flight_path/generate_circle_path.py) flags. يأخذ
samples من دائرة نصف قطرها 0.5 متر بخطوة 0.1 radian، ويكتبها في
`flight_path/circle_coordinates.pkl`.

```bash
uv run python flight_path/fly_with_generated_path.py flight_path/circle_coordinates.pkl
uv run python flight_path/fly_with_generated_path.py flight_path/circle_coordinates.pkl --flight
```

يعرض [fly_with_generated_path.py](flight_path/fly_with_generated_path.py) سلسلة
pickle من إحداثيات `(x, y)` بالمتر. وعند تفعيل الطيران يرسل كل نقطة إلى الطائرة
بالصيغة `(x, 0, y + 0.5)`.

- `pickle_path`: مسار ملف pickle، وهو argument إلزامي.
- `--flight` / `--no-flight`: تفعيل أو تعطيل الحركة الحقيقية؛ الافتراضي معطّل.
  عند التفعيل، اكتب `y` ثم اضغط `a` لتنفيذ arm و`t` للإقلاع. أثناء المسار ينفّذ
  `0` أمر disarm ويوقف `q` المسار؛ اضغط `q` مرة أخرى في النافذة الأخيرة.

### مسار نصي

```bash
cd flight_path
uv run python generate_text_cords.py
cd ..
```

يستخدم [generate_text_cords.py](flight_path/generate_text_cords.py) مكتبة FreeType
لاستخراج outline الحرف `S` المكتوب مباشرة في source من خط JetBrains Mono Nerd
Font، ثم يأخذ samples من الخطوط والمنحنيات التربيعية ويعمل normalize إلى 0.75
وحدة، ويكتب `text-cords.pkl`. لا توجد flags؛ يُعدّل الخط والحرف وprecision في source.

## أمثلة AprilTag / ArUco

تستخدم هذه الأمثلة `cv2.aruco`. شغّل برامج detection من داخل `april_tag/` لأن
مسارات calibration نسبية. يفترض pose estimation أن طول ضلع التاغ الحقيقي 0.1 متر.

### إنشاء marker

```bash
cd april_tag
uv run python april_tag_gen.py -o tag.png -i 7 [-t DICTIONARY] [-p PIXELS]
cd ..
```

ينشئ [april_tag_gen.py](april_tag/april_tag_gen.py) marker بحجم 300x300 بواسطة
OpenCV، ويضيف padding ثم يحفظه ويعرضه.

- `-o`، `--output`: مسار صورة الناتج، إلزامي.
- `-i`، `--id`: معرّف marker صالح ضمن dictionary المختار، إلزامي.
- `-t`، `--type`: الافتراضي `DICT_ARUCO_ORIGINAL`. يدعم عائلات OpenCV من
  `DICT_4X4_*` إلى `DICT_7X7_*`، و`DICT_ARUCO_ORIGINAL`، وأسماء AprilTag
  `16h5` و`25h9` و`36h10` و`36h11`.
- `-p`، `--padding`: الهامش الأبيض بالـ pixels، وافتراضياً `50`؛ تلغيه القيمة `0`.

### اكتشاف marker وعرض pose

```bash
cd april_tag
uv run python april_tag_detect.py [-c CAMERA] [-t DICTIONARY]
cd ..
```

يكتشف [april_tag_detect.py](april_tag/april_tag_detect.py) الـ markers، ويحسب
translation وrotation عبر OpenCV `solvePnP` وبيانات calibration المحفوظة، ويعرض
pose باستخدام OpenCV وPyVista.

- `-c`، `--cam`: القيمة `robeex` (افتراضياً) أو رقم webcam مثل `0`؛ ويختار
  `calibration_data_robeex.npz` أو `calibration_data_pc.npz` على الترتيب.
- `-t`، `--type`: اسم dictionary، وافتراضياً `DICT_5X5_100`.

ينتظر التنفيذ الحالي telemetry من RoBeeX حتى عند اختيار كاميرا محلية. الخروج بـ `q`.

### نشر pose عبر WebSocket

```bash
cd april_tag
uv run python april_tag_3d.py [-c CAMERA] [-t DICTIONARY] [--multi-tag]
cd ..
```

يستخدم [april_tag_3d.py](april_tag/april_tag_3d.py) الملف
[app_aruco_detector.py](april_tag/app_aruco_detector.py) لحساب pose، والملف
[ws_server.py](april_tag/ws_server.py) لنشر telemetry على
`ws://127.0.0.1:8686` وJSON الخاص بالتاغ على `ws://127.0.0.1:8687`.

- `-c`، `--cam`: `robeex` أو رقم webcam.
- `-t`، `--type`: اسم dictionary، وافتراضياً `DICT_5X5_100`.
- `-mt`، `--multi-tag` / `--no-multi-tag`: نشر جميع التاغات بدلاً من الأول؛
  معطّل افتراضياً. يُفضّل الشكل الطويل بسبب تسمية `BooleanOptionalAction` في `argparse`.

استخدم `.` للخروج مع كاميرا RoBeeX، أو `q` مع الكاميرا المحلية.

### معاينة calibration وأدوات WebSocket المساعدة

```bash
uv run python april_tag/calibration.py
```

يفتح [calibration.py](april_tag/calibration.py) الـ webcam رقم `0` ويعرض اكتشاف
chessboard ذي 7x6 زوايا داخلية. هذه معاينة فقط؛ لا يحسب البرنامج calibration ولا
يحفظه. اضغط `q` للخروج.

يعرّف [ws_server.py](april_tag/ws_server.py) الكلاس `BroadcastServer`، بينما أُعد
[test_ws.py](april_tag/test_ws.py) لنشر telemetry تجريبية. لا يمرّر الـ standalone
block في أي منهما argument الإلزامي `port`، لذا يؤدي تشغيلهما مباشرة إلى
`TypeError`؛ اعتبرهما ملفات مساعدة لا أوامر مستقلة.

## المساهمة

نرحب بالـ issues والـ pull requests وأي إصلاحات مقترحة.
