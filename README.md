# OBS Projector Style Timer

A local OBS Browser Source timer that looks like cool-white projector light on a gray wall. It includes five brightness levels, bloom/blur controls, and optional auto-pause when you leave frame.

No video is uploaded. The helper only exposes local status at `127.0.0.1`.

## Install

1. Download this repo as a ZIP and extract it.
2. Double-click `INSTALL - OBS Projector Timer.bat`.
3. Open OBS.
4. Add a `Browser Source`.
5. Enable `Local file`.
6. Select `obs-projector-timer.html`.
7. Set width/height to your canvas, usually `1920 x 1080`.

The installer starts the helper quietly and adds it to Windows startup. It uses automatic camera detection; you do not need to choose a camera number.

The timer starts fresh at `00:00:00` when the browser source loads.

## Daily Use

Open OBS. The helper should already be running in the background.

If OBS is already using your webcam, click `Start Virtual Camera` in OBS. The helper keeps trying quietly until it finds a working camera feed.

To stop the background helper, double-click `stop-helper.bat`.

## Auto-Pause

Step fully out of frame for about 3 seconds. The timer pauses and shows `bathroom break`. It resumes when you return.

To check the helper, double-click `check-status.bat`.

Good status: `camera_ok` is `true`.

Waiting status: the helper is running, but no camera feed is available yet. Start OBS Virtual Camera if OBS owns the webcam.

## Controls

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
2. Double-click `check-status.bat`.
3. If it is still waiting, double-click `INSTALL - OBS Projector Timer.bat` again.

`find-camera-indexes.bat` is only for advanced troubleshooting. Normal setup does not require camera numbers.

## Optional Saved Timer

By default, the timer starts fresh each load. To keep elapsed time between reloads, add this to the OBS Browser Source URL:

```text
?save=1
```

Most users should leave this off.
