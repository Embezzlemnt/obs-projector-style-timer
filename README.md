# OBS Projector Style Timer

A local OBS Browser Source timer that looks like cool-white projector light on a gray wall. It includes five brightness levels, bloom/blur controls, and optional auto-pause when you leave frame.

No video is uploaded. The helper only exposes local status at `127.0.0.1`.

## Install Once

1. Download this repo as a ZIP and extract it.
2. Install Python 3.
3. Install OpenCV:

```bat
pip install opencv-python
```

4. Open OBS.
5. If OBS already uses your webcam, click `Start Virtual Camera`.
6. Double-click `setup-auto-pause.bat`.
7. A `camera-previews` folder opens.
8. Pick the number from the image that shows the camera feed you want.
   Example: if `camera-index-1.jpg` is correct, type `1`.
9. In OBS, add a `Browser Source`.
10. Enable `Local file`.
11. Select `obs-projector-timer.html`.
12. Set width/height to your canvas, usually `1920 x 1080`.

The timer starts fresh at `00:00:00` when the browser source loads.

## Daily Use

1. Open OBS.
2. Start OBS Virtual Camera if your webcam is already used in OBS.
3. Double-click `start-helper-hidden.vbs`.

That is it. The helper runs quietly in the background.

To make the helper start with Windows, run:

```text
install-autostart.bat
```

## Check Auto-Pause

Run:

```text
check-status.bat
```

Good:

```json
"camera_ok": true
```

Then step fully out of frame for about 3 seconds. The timer should pause and show `bathroom break`. It resumes when you return.

## Camera Number

A camera number is the number the helper uses to open a camera-like device.

```text
0 = maybe your webcam
1 = maybe OBS Virtual Camera
2 = maybe another camera/capture device
```

Do not guess. Use `setup-auto-pause.bat`, then choose by preview image:

```text
camera-index-0.jpg
camera-index-1.jpg
camera-index-2.jpg
```

Pick the image that shows the feed you want the helper to watch.

## OBS Interact Controls

Right-click the Browser Source and choose `Interact`.

```text
1 = dim / night
2 = normal
3 = bright / day
4 = strong projector
5 = ultra projector
Arrow Up = brighter
Arrow Down = dimmer
Arrow Right = more bloom and blur
Arrow Left = less bloom and blur
0 = manual bathroom break
R = reset timer to 00:00:00
```

## Troubleshooting

If auto-pause does not work:

1. Start OBS Virtual Camera.
2. Run `setup-auto-pause.bat`.
3. Pick the correct preview image number.
4. Run `check-status.bat`.

If `camera_ok` is still false, choose a different preview image number or close other apps using the webcam.

## Optional Saved Timer

By default, the timer starts fresh each load. To keep elapsed time between reloads, add this to the OBS Browser Source URL:

```text
?save=1
```

Most users should leave this off.
