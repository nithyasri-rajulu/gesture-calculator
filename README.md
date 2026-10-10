# Gesture Controlled Virtual Calculator

![Demonstration output](outputs/preview.png)

## What it does

OpenCV captures and mirrors webcam frames. A pretrained MediaPipe Hand Landmarker supplies fingertip and palm coordinates. The index fingertip selects a screen key. Thumb-index distance, divided by palm width, controls a pinch gate with separate close/release thresholds. A stable hover is required, a held pinch produces at most one event, and loss of tracking disarms the gate. Arithmetic is parsed through a small allowlisted AST evaluator; Python eval is never used.

## Quick start

Tested with Python 3.12 on Linux. These commands run without a camera or graphical display.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
source .venv/bin/activate  # Linux / WSL
python -m pip install -r requirements-dev.txt
python -m pytest -q
python app.py --demo
```

On Windows, replace the `source` line with the PowerShell activation command shown in the comment. On systems where the executable is named `python3`, use it for the first command. The demo writes `outputs/results.json` and visual outputs. No private images or industrial datasets are required.

## Verified result

16 unit tests passed. A scripted sequence produced exactly five key activations and calculated 12 + 8 = 20. The replay validates input gating and arithmetic, not camera hand-detection accuracy. Live webcam use needs validation on the user's machine.

## Webcam or mouse mode

Use a separate environment with display-capable OpenCV; do not install it alongside the headless package. On Windows, native Python usually makes webcam access simpler than WSL.

```bash
python -m venv .camera-venv
# Windows: .camera-venv\Scripts\activate
source .camera-venv/bin/activate  # Linux
python -m pip install -r requirements-camera.txt
python download_model.py
python app.py --model models/hand_landmarker.task
# Mouse fallback, without a model or camera:
python app.py --mouse
```

Move the index fingertip over a key, open the thumb-index pinch, hover briefly, then pinch. Release before the next selection. Press Q or Escape to exit. Camera index defaults to 0; try `--camera 1` when needed. Model downloads are explicit and their SHA-256 is recorded locally.


## Files

- `app.py`: CLI, input handling, synthetic demo and output generation.
- Core module: reusable algorithm and validation logic.
- `tests/`: regression checks including failure conditions.
- `outputs/`: generated evidence from the included experiment.
- `REPORT.md`: project rationale, method, evaluation and limitations.


- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/python
- https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/index
- https://docs.opencv.org/4.13.0/d8/dfe/classcv_1_1VideoCapture.html
