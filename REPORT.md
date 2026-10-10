# Gesture Controlled Virtual Calculator Project Report

## Engineering approach

OpenCV captures and mirrors webcam frames. A pretrained MediaPipe Hand Landmarker supplies fingertip and palm coordinates. The index fingertip selects a screen key. Thumb-index distance, divided by palm width, controls a pinch gate with separate close/release thresholds. A stable hover is required, a held pinch produces at most one event, and loss of tracking disarms the gate. Arithmetic is parsed through a small allowlisted AST evaluator; Python eval is never used.

## Reproduction

Install the pinned development requirements in a clean Python 3.12 environment. Run `python -m pytest -q`, then `python app.py --demo`. Configuration, fixed seeds and ground-truth generation are visible in `app.py`. Actual outputs are recorded in `outputs/results.json`.

## Evaluation

16 unit tests passed. A scripted sequence produced exactly five key activations and calculated 12 + 8 = 20. The replay validates input gating and arithmetic, not camera hand-detection accuracy. Live webcam use needs validation on the user's machine.

![Pipeline output](outputs/preview.png)



## References

- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python
- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/index
- https://docs.opencv.org/4.13.0/d8/dfe/classcv_1_1VideoCapture.html
