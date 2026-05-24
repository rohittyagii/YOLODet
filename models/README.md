Place YOLO face detection model weights in this folder.

Expected default path:
- models/yolov8n-face.pt

You can use any YOLO face model compatible with ultralytics and set custom path:
- Windows PowerShell:
  $env:YOLO_FACE_MODEL = "models/your-face-model.pt"

Then run:
- python web_yolo_app.py

If /health reports model not found, verify the file path and name.
