# Real-Time YOLO Browser Detection (Python + Flask)

A web-first YOLO detection app that runs Ultralytics inference in a Python backend
and streams webcam frames from the browser.

## 1) Project Structure

```text
Real-Time-Image-Processing-Toolkit/
|-- launch_web_yolo.py
|-- run.py
|-- web_yolo_app.py
|-- requirements.txt
|-- web/
|   `-- index.html
|-- models/
|-- outputs/
```

## 2) Installation

Use a single command from the VS Code terminal:

```bash
python run.py
```

What this does automatically:
- Creates `.venv` if it does not exist
- Installs/updates all packages from `requirements.txt`
- Launches the web app

Portable launcher options (works even if terminal starts in a different folder):

```bash
python /full/path/to/project/run.py
```

Windows double-click / terminal helper:

```text
start.bat
```

`start.bat` opens an interactive setup wizard and starts the selected mode.

## 3) Run

Default web mode (opens browser):

```bash
python run.py
```

Setup wizard mode (recommended for first run on a new PC):

```bash
python run.py --wizard
```

Setup only (install dependencies and exit):

```bash
python run.py --setup-only
```

Backend-only mode (no auto browser open):

```bash
python run.py --mode backend
```

Open browser at:

```text
http://127.0.0.1:5000
```

In the web UI:
- Select a provider from Model Provider list.
- Click Apply Provider.
- Click Start Detection.

Notes:
- `Ultralytics YOLOv8n` and `YOLO11n` auto-download on first use.
- For face-specific detection, use Local Face Model or Custom URL provider.

## 4) Features Included

- Browser webcam access via `getUserMedia`
- Python backend runs YOLO inference via Ultralytics
- Real-time bounding boxes and confidence overlay in browser
- Backend health endpoint at `/health`
- Detection endpoint at `/detect`
- Model provider endpoints: `/model/providers` and `/model/select`

## 5) Common Errors and Fixes

1. YOLO backend says model not found
- Cause: Missing model weights file.
- Fix:
  - Place model file at `models/yolov8n-face.pt`, or
  - Set environment variable `YOLO_MODEL_REF` to your model path/name.

2. YOLO provider apply fails
- Cause: Invalid custom URL or blocked download.
- Fix:
  - Try built-in provider `Ultralytics YOLOv8n` first.
  - Verify custom URL is a direct `.pt` file link.
  - Check internet connectivity/firewall.

3. Browser camera permission denied
- Cause: Browser blocked camera access.
- Fix:
  - Allow camera access in browser settings.
  - Close other apps using the camera.
  - Check Windows camera privacy settings.
