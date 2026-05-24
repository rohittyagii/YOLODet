# Performance Log

Date: 2026-05-24

## Changes
- No algorithmic performance changes applied in this pass.

## Notes
- Web detection cadence is driven by a 120 ms timer (~8 FPS). If higher throughput is needed, consider adaptive scheduling that waits for inference completion before sending the next frame.
