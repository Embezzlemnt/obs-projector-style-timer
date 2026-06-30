import argparse
import contextlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

os.environ.setdefault("OPENCV_LOG_LEVEL", "SILENT")
import cv2


try:
    cv2.setLogLevel(0)
except Exception:
    pass


state_lock = threading.Lock()
state = {
    "camera_ok": False,
    "camera": "auto",
    "paused": False,
    "presence": 0.0,
    "face_count": 0,
    "body_count": 0,
    "skin_ratio": 0.0,
    "last_seen_seconds": None,
    "error": "",
}


DEFAULT_SETTINGS = {
    "camera": "auto",
    "port": 8765,
    "pause": 3.0,
    "resume": 0.5,
    "interval": 0.12,
    "presence_threshold": 0.42,
}


def clamp(value, low, high):
    return max(low, min(high, value))


@contextlib.contextmanager
def muted_native_stderr(enabled=True):
    if not enabled:
        yield
        return

    try:
        sys.stderr.flush()
        saved = os.dup(2)
        with open(os.devnull, "w", encoding="utf-8") as devnull:
            os.dup2(devnull.fileno(), 2)
            try:
                yield
            finally:
                sys.stderr.flush()
                os.dup2(saved, 2)
                os.close(saved)
    except Exception:
        yield


def load_settings():
    settings_path = Path(__file__).with_name("timer-helper-settings.json")
    settings = dict(DEFAULT_SETTINGS)
    if not settings_path.exists():
        return settings

    try:
        loaded = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return settings

    aliases = {
        "camera_index": "camera",
        "presenceThreshold": "presence_threshold",
    }
    for key, value in loaded.items():
        normalized = aliases.get(key, key)
        if normalized in settings:
            settings[normalized] = value
    return settings


def parse_camera_setting(value):
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in ("", "auto", "default", "any"):
        return None
    try:
        return int(text)
    except ValueError:
        return None


def camera_candidates(preferred):
    chosen = parse_camera_setting(preferred)
    numbers = []
    if chosen is not None:
        numbers.append(chosen)
    for index in range(9):
        if index not in numbers:
            numbers.append(index)
    return numbers


def open_camera(index):
    backends = []
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)
    backends.append(0)

    for backend in backends:
        with muted_native_stderr():
            cap = cv2.VideoCapture(index, backend) if backend else cv2.VideoCapture(index)
            opened = cap.isOpened()
        if opened:
            with muted_native_stderr():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
                cap.set(cv2.CAP_PROP_FPS, 15)
                ok, _ = cap.read()
            if ok:
                return cap
            cap.release()
    return None


def open_first_available_camera(preferred):
    for index in camera_candidates(preferred):
        cap = open_camera(index)
        if cap is not None:
            return index, cap
    return None, None


def read_frame(index):
    cap = open_camera(index)
    if cap is None:
        return None
    try:
        for _ in range(5):
            ok, frame = cap.read()
            if ok:
                return frame
            time.sleep(0.05)
        return None
    finally:
        cap.release()


def windows_camera_names():
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        (
            "Get-CimInstance Win32_PnPEntity | "
            "Where-Object { $_.Name -match 'Camera|Webcam|Video|OBS|Virtual' } | "
            "Select-Object -ExpandProperty Name"
        ),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=6)
    except Exception:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def load_cascade(name):
    path = cv2.data.haarcascades + name
    cascade = cv2.CascadeClassifier(path)
    return None if cascade.empty() else cascade


def resize_for_detection(frame, max_width=640):
    height, width = frame.shape[:2]
    if width <= max_width:
        return frame
    scale = max_width / float(width)
    return cv2.resize(frame, (max_width, int(height * scale)), interpolation=cv2.INTER_AREA)


def detect_with(cascade, gray, scale=1.06, neighbors=4, min_size=(42, 42)):
    if cascade is None:
        return []
    found = cascade.detectMultiScale(
        gray,
        scaleFactor=scale,
        minNeighbors=neighbors,
        minSize=min_size,
    )
    return list(found)


def skin_ratio(frame):
    height, width = frame.shape[:2]
    roi = frame[int(height * 0.10):int(height * 0.92), int(width * 0.18):int(width * 0.82)]
    ycrcb = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)
    mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
    return float(cv2.countNonZero(mask)) / float(mask.size)


def looks_like_obs_standby(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(hsv, (95, 35, 25), (135, 255, 230))
    white = cv2.inRange(hsv, (0, 0, 170), (179, 55, 255))
    blue_ratio = float(cv2.countNonZero(blue)) / float(blue.size)
    white_ratio = float(cv2.countNonZero(white)) / float(white.size)
    return blue_ratio > 0.62 and 0.006 < white_ratio < 0.08


def detect_loop(args):
    face_cascades = [
        load_cascade("haarcascade_frontalface_default.xml"),
        load_cascade("haarcascade_frontalface_alt.xml"),
        load_cascade("haarcascade_frontalface_alt2.xml"),
    ]
    profile = load_cascade("haarcascade_profileface.xml")
    upperbody = load_cascade("haarcascade_upperbody.xml")
    cap = None
    active_camera = None
    last_seen = time.monotonic()
    last_missing = None
    last_object_seen = 0.0
    present_since = time.monotonic()
    paused = False
    smoothed_confidence = 0.0

    while True:
        if cap is None:
            active_camera, cap = open_first_available_camera(args.camera)
            if cap is None:
                now = time.monotonic()
                with state_lock:
                    state.update({
                        "camera_ok": False,
                        "camera": "searching",
                        "paused": paused,
                        "presence": 0.0,
                        "face_count": 0,
                        "body_count": 0,
                        "skin_ratio": 0.0,
                        "last_seen_seconds": round(now - last_seen, 2) if last_seen else None,
                        "error": "Waiting for a camera feed. If OBS uses the webcam, start OBS Virtual Camera; the helper will connect automatically.",
                    })
                time.sleep(2.0)
                continue

            with state_lock:
                state.update({
                    "camera_ok": True,
                    "camera": active_camera,
                    "error": "",
                })
            smoothed_confidence = 0.0
            last_object_seen = time.monotonic()

        ok, frame = cap.read()
        now = time.monotonic()

        if not ok:
            cap.release()
            cap = None
            with state_lock:
                state.update({
                    "camera_ok": False,
                    "camera": "reconnecting",
                    "presence": 0.0,
                    "error": "Camera feed paused or became busy. Reconnecting automatically.",
                })
            time.sleep(1.0)
            continue

        frame = resize_for_detection(frame)
        if looks_like_obs_standby(frame):
            with state_lock:
                state.update({
                    "camera_ok": False,
                    "camera": active_camera,
                    "paused": False,
                    "presence": 0.0,
                    "face_count": 0,
                    "body_count": 0,
                    "skin_ratio": 0.0,
                    "last_seen_seconds": None,
                    "error": "OBS Virtual Camera is showing its standby screen. Start OBS Virtual Camera on the scene with your camera feed.",
                })
            smoothed_confidence = 0.0
            last_missing = None
            time.sleep(args.interval)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = []
        for cascade in face_cascades:
            faces.extend(detect_with(cascade, gray, scale=1.06, neighbors=4, min_size=(38, 38)))
        if profile is not None:
            faces.extend(detect_with(profile, gray, scale=1.08, neighbors=4, min_size=(42, 42)))
            flipped = cv2.flip(gray, 1)
            faces.extend(detect_with(profile, flipped, scale=1.08, neighbors=4, min_size=(42, 42)))

        bodies = detect_with(upperbody, gray, scale=1.08, neighbors=5, min_size=(90, 90))

        current_skin = skin_ratio(frame)
        face_count = len(faces)
        body_count = len(bodies)
        face_presence = 1.0 if face_count else 0.0
        body_presence = 0.72 if body_count else 0.0
        if face_count or body_count:
            last_object_seen = now

        if current_skin >= 0.09:
            skin_presence = 0.48
        elif current_skin >= 0.04:
            skin_presence = 0.24
        else:
            skin_presence = 0.0

        recent_object = now - last_object_seen < 1.45
        continuity_presence = 0.50 if recent_object and skin_presence > 0 else 0.0
        raw_confidence = clamp(max(face_presence, body_presence, skin_presence, continuity_presence), 0.0, 1.0)
        smoothing = 0.62 if raw_confidence > smoothed_confidence else 0.22
        smoothed_confidence = smoothed_confidence + (raw_confidence - smoothed_confidence) * smoothing
        confidence = clamp(smoothed_confidence, 0.0, 1.0)

        enter_threshold = args.presence_threshold
        stay_threshold = max(0.28, args.presence_threshold - 0.16)
        present = confidence >= enter_threshold or (last_missing is None and confidence >= stay_threshold)

        if present:
            if present_since is None:
                present_since = now
            last_seen = now
            last_missing = None
            if paused and now - present_since >= args.resume:
                paused = False
        else:
            present_since = None
            if last_missing is None:
                last_missing = now
            if not paused and now - last_missing >= args.pause:
                paused = True

        with state_lock:
            state.update({
                "camera_ok": True,
                "camera": active_camera,
                "paused": paused,
                "presence": round(confidence, 3),
                "face_count": face_count,
                "body_count": body_count,
                "skin_ratio": round(current_skin, 4),
                "last_seen_seconds": round(now - last_seen, 2),
                "error": "",
            })

        time.sleep(args.interval)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/", "/state", "/state.json"):
            self.send_response(404)
            self.end_headers()
            return

        with state_lock:
            payload = dict(state)
        body = json.dumps(payload).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        return


def main():
    defaults = load_settings()
    parser = argparse.ArgumentParser(description="Camera-based auto-pause helper for OBS timer.")
    parser.add_argument("--camera", default=str(defaults["camera"]), help="Camera number or auto. Default: auto.")
    parser.add_argument("--scan", action="store_true", help="Scan camera numbers 0-8 and exit.")
    parser.add_argument("--save-previews", action="store_true", help="Save preview JPGs for available camera numbers during scan.")
    parser.add_argument("--port", type=int, default=int(defaults["port"]), help="Local HTTP port.")
    parser.add_argument("--pause", type=float, default=float(defaults["pause"]), help="Seconds out of frame before pausing.")
    parser.add_argument("--resume", type=float, default=float(defaults["resume"]), help="Seconds in frame before resuming.")
    parser.add_argument("--interval", type=float, default=float(defaults["interval"]), help="Camera sampling interval in seconds.")
    parser.add_argument("--presence-threshold", type=float, default=float(defaults["presence_threshold"]), help="Presence confidence threshold.")
    args = parser.parse_args()

    if args.scan:
        names = windows_camera_names()
        if names:
            print("Windows camera/video devices:")
            for name in names:
                print(f"  - {name}")
            print("")
        else:
            print("No Windows camera/video device names found.")
            print("")
        print("Scanning camera numbers 0-8...")
        preview_dir = Path(__file__).with_name("camera-previews")
        if args.save_previews:
            preview_dir.mkdir(exist_ok=True)
            for old_preview in preview_dir.glob("camera-index-*.jpg"):
                old_preview.unlink(missing_ok=True)

        for index in range(9):
            frame = read_frame(index)
            if frame is None:
                print(f"{index}: unavailable")
            else:
                print(f"{index}: available")
                if args.save_previews:
                    label = f"camera number {index}"
                    cv2.putText(frame, label, (20, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 3, cv2.LINE_AA)
                    cv2.imwrite(str(preview_dir / f"camera-index-{index}.jpg"), frame)

        if args.save_previews:
            print("")
            print(f"Preview images saved to: {preview_dir}")
            print("Open that folder and choose the number whose image shows the feed you want.")
        return

    worker = threading.Thread(target=detect_loop, args=(args,), daemon=True)
    worker.start()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"OBS auto-pause helper running: http://127.0.0.1:{args.port}/state")
    print(f"Camera: {args.camera} | pause: {args.pause}s | resume: {args.resume}s")
    print("Leave this window open while OBS is running. Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
