# Architecture Map

## Entry Points
- `run.py`: creates venv, installs dependencies, launches selected mode.
- `launch_web_yolo.py`: starts Flask backend and opens browser.
- `web_yolo_app.py`: Flask backend for YOLO detection.

## Web UI
- `web/index.html`: browser UI, webcam capture, inference loop, overlay rendering.

## Data Flow (Web YOLO)
- Browser captures webcam frame -> POST /detect -> YOLO inference -> boxes rendered in canvas overlay.
