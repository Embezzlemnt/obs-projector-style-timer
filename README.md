# OBS Projector Style Timer

A premium OBS Browser Source timer that looks like cool-white projector light cast onto a gray wall. It includes soft bloom, optical blur, feathered wall wash, keyboard controls, and an optional local auto-pause helper for bathroom breaks.

The timer itself is a local HTML file. Auto-pause is handled by a small local Python helper because OBS Browser Sources often cannot access the same webcam OBS is already using.

## What You Get

- Projector-style `DESK TIME` timer for OBS
- Five brightness levels for different room lighting
- Bloom and blur controls from OBS Interact
- Automatic pause when you leave frame
- `bathroom break` text while paused
- Quiet background helper with no command window
- No cloud service, no tracking, no network dependency beyond local `127.0.0.1`

## Requirements

- Windows
- OBS Studio
- Python 3
- OpenCV for Python:

```bat
pip install opencv-python
```

## Quick Setup

1. Download this repository as a ZIP and extract it.
2. Open OBS.
3. If OBS already uses your webcam, click `Start Virtual Camera` in OBS.
4. Double-click `setup-auto-pause.bat`.
5. Look at the preview images it opens.
6. Choose the number whose preview image shows the feed you want.
7. In OBS, add a `Browser Source`.
8. Enable `Local file`.
9. Select `obs-projector-timer.html`.
10. Set width/height to your OBS canvas, usually `1920 x 1080`.

The setup script starts the auto-pause helper quietly in the background.

## Daily Use

Before recording or streaming:

1. Open OBS.
2. Make sure OBS Virtual Camera is started if your physical webcam is already used in OBS.
3. Double-click `start-helper-hidden.vbs`.

To make the helper start with Windows, double-click:

```text
install-autostart.bat
```

To remove startup:

```text
remove-autostart.bat
```

## Auto-Pause Test

Run:

```text
check-status.bat
```

You want:

```json
"camera_ok": true
```

Then walk fully out of frame for about 3 seconds. The timer should pause and display:

```text
bathroom break
```

When you return, it should resume.

## What Is A Camera Index?

A camera index is just the number OpenCV/Windows uses to open a camera-like device.

Examples:

```text
0 = maybe your physical webcam
1 = maybe OBS Virtual Camera
2 = maybe another capture device
```

Windows does not always expose friendly camera names to OpenCV, and the order can change when OBS Virtual Camera starts or stops. That is why the setup script scans indexes and saves preview images.

When `setup-auto-pause.bat` opens the `camera-previews` folder, pick the number in the image filename:

```text
camera-index-0.jpg
camera-index-1.jpg
camera-index-2.jpg
```

Choose the index whose preview shows the feed you want the helper to watch. If OBS is using your real webcam, start OBS Virtual Camera and choose the preview that shows the OBS Virtual Camera output.

## OBS Interact Controls

Right-click the Browser Source in OBS and choose `Interact`.

Use:

```text
1 = dim / night
2 = normal
3 = bright / day
4 = strong projector
5 = ultra projector
Arrow Up = one level brighter
Arrow Down = one level dimmer
Arrow Right = more bloom and blur
Arrow Left = less bloom and blur
0 = manual bathroom break toggle
```

The controls are silent. No debug text appears on stream.

## Troubleshooting Auto-Pause

If auto-pause does not work:

1. In OBS, click `Start Virtual Camera`.
2. Run `setup-auto-pause.bat`.
3. Look at the preview images.
4. Choose the index whose preview shows the right feed.
5. Run `check-status.bat`.

If `camera_ok` is false, choose another available camera index.

If every camera index is unavailable, another app may have exclusive control of the camera. Close camera apps, restart OBS Virtual Camera, and run setup again.

## Settings

`timer-helper-settings.json` controls the helper:

```json
{
  "camera": 0,
  "port": 8765,
  "pause": 3.0,
  "resume": 0.5,
  "interval": 0.12,
  "presence_threshold": 0.32
}
```

Most users only need to change `camera`, and `setup-auto-pause.bat` does that for you.

## Safety

The helper only serves a tiny local status JSON at:

```text
http://127.0.0.1:8765/state
```

It does not upload video or send camera data anywhere.
