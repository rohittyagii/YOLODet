# Bug Tracker

Date: 2026-05-24

## Fixed
- Web YOLO backend returned 500 when `class_ids` contained non-integers. Added safe parsing and validation.
- Browser preflight camera stream could lock the device before Start. Now releases tracks immediately.

## Open
- None identified during static review. Run the app to surface runtime-only issues (drivers, model downloads, camera permissions).
