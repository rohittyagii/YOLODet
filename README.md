# YOLODet

[![CI](https://github.com/rohittyagii/YOLODet/actions/workflows/ci.yml/badge.svg)](https://github.com/rohittyagii/YOLODet/actions/workflows/ci.yml)

YOLODet is a browser-based YOLO detection app. A Python backend
runs Ultralytics inference while your browser streams webcam frames.

## Quick Start 

1) Open a terminal in this folder.

2) Run:

```bash
python run.py
```

This single command:
- Creates a virtual environment if needed
- Installs requirements from `requirements.txt`
- Starts the web app

3) Open your browser at:

```text
http://127.0.0.1:5000
```

4) In the web page:
- Choose a Model Provider
- Click Apply Provider
- Click Start Detection

Tip: `Ultralytics YOLOv8n` and `YOLO11n` auto-download their weights the first time.

## Project Structure (What is where)

```text
YOLODet/
|-- launch_web_yolo.py
|-- run.py
|-- web_yolo_app.py
|-- requirements.txt
|-- web/
|   `-- index.html
|-- models/
|-- outputs/
```

## Run Modes (Optional)

Setup wizard (good for a first-time PC):

```bash
python run.py --wizard
```

Setup only (install dependencies, then exit):

```bash
python run.py --setup-only
```

Backend-only (no browser auto-open):

```bash
python run.py --mode backend
```

## Beginner Glossary

- Model weights: The `.pt` files that contain what the model learned.
- Inference: The model making predictions on an image.
- Confidence: How sure the model is about a detection.
- IoU: Overlap score used to filter duplicates.

## API (Simple Overview)

- `GET /health` - Is the backend ready?
- `POST /detect` - Send an image, get detections back
- `GET /model/providers` - List model options
- `POST /model/select` - Pick or download a model

## Common Errors and Fixes

1) Model not found
- Fix: Use a built-in provider first, or place a `.pt` file in `models/` and select it.

2) Model download fails
- Fix: Check internet access and try a direct `.pt` URL.

3) Camera permission denied
- Fix: Allow camera access in your browser and close other camera apps.

## CI Note

The GitHub Actions workflow only checks Python syntax (compile step). It does not
download large model files or run the webcam.
