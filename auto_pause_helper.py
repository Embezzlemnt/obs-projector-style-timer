import argparse
import json
from pathlib import Path
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

import cv2


try:
    cv2.setLogLevel(0)
except Exception:
    pass


state_lock = threading.Lock()
state = {
    "camera_ok": False,
    "paused": False,
    "presence": 0.0,
    "face_count": 0,
    "skin_ratio": 0.0,
    "last_seen_seconds": None,
    "error": "",
}


DEFAULT_SETTINGS = {
    "camera": 0,
    "port": 8765,
    "pause": 3.0,
    "resume": 0.5,
    "interval": 0.12,
    "presence_threshold": 0.32,
}


def clamp(value, low, high):
    return max(low, min(high, value))


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


def open_camera(index):
    backends = []
    if hasattr(cv2, "CAP_DSHOW"):
        backends.append(cv2.CAP_DSHOW)
    if hasattr(cv2, "CAP_MSMF"):
        backends.append(cv2.CAP_MSMF)
    backends.append(0)

    for backend in backends:
        cap = cv2.VideoCapture(index, backend) if backend else cv2.VideoCapture(index)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
            cap.set(cv2.CAP_PROP_FPS, 15)
            ok, _ = cap.read()
            if ok:
                return cap
            cap.release()
    return None


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


def skin_ratio(frame):
    height, width = frame.shape[:2]
    roi = frame[int(height * 0.10):int(height * 0.92), int(width * 0.18):int(width * 0.82)]
    ycrcb = cv2.cvtColor(roi, cv2.COLOR_BGR2YCrCb)
    mask = cv2.inRange(ycrcb, (0, 133, 77), (255, 173, 127))
    return float(cv2.countNonZero(mask)) / float(mask.size)


def detect_loop(args):
    frontal = load_cascade("haarcascade_frontalface_default.xml")
    profile = load_cascade("haarcascade_profileface.xml")
    cap = open_camera(args.camera)

    if cap is None:
        with state_lock:
            state.update({
                "camera_ok": False,
                "paused": False,
                "presence": 0.0,
                "error": f"Could not open camera index {args.camera}. Try --camera 1 or close apps using the webcam.",
            })
        return

    skin_baseline = 0.0
    last_seen = time.monotonic()
    last_missing = None
    present_since = time.monotonic()
    paused = False

    with state_lock:
        state.update({"camera_ok": True, "error": ""})

    while True:
        ok, frame = cap.read()
        now = time.monotonic()

        if not ok:
            with state_lock:
                state.update({
                    "camera_ok": False,
                    "error": "Camera frame read failed.",
                })
            time.sleep(0.25)
            continue

        frame = cv2.resize(frame, (640, 360))
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = []
        if frontal is not None:
            faces.extend(frontal.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(42, 42)))
        if profile is not None:
            faces.extend(profile.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=5, minSize=(42, 42)))
            flipped = cv2.flip(gray, 1)
            faces.extend(profile.detectMultiScale(flipped, scaleFactor=1.08, minNeighbors=5, minSize=(42, 42)))

        current_skin = skin_ratio(frame)
        face_count = len(faces)
        if face_count:
            skin_baseline = max(current_skin, skin_baseline * 0.92 + current_skin * 0.08)

        skin_presence = 0.0
        if skin_baseline > 0.005:
            skin_presence = clamp(current_skin / max(0.012, skin_baseline * 0.48), 0.0, 1.0)

        face_presence = 1.0 if face_count else 0.0
        confidence = clamp(face_presence * 0.82 + skin_presence * 0.34, 0.0, 1.0)
        present = confidence >= args.presence_threshold

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
                "paused": paused,
                "presence": round(confidence, 3),
                "face_count": face_count,
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
    parser.add_argument("--camera", type=int, default=int(defaults["camera"]), help="Camera index. Try 1 or 2 if 0 is busy.")
    parser.add_argument("--scan", action="store_true", help="Scan camera indexes 0-8 and exit.")
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
        print("Scanning camera indexes 0-8...")
        for index in range(9):
            cap = open_camera(index)
            if cap is None:
                print(f"{index}: unavailable")
            else:
                print(f"{index}: available")
                cap.release()
        return

    worker = threading.Thread(target=detect_loop, args=(args,), daemon=True)
    worker.start()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"OBS auto-pause helper running: http://127.0.0.1:{args.port}/state")
    print(f"Camera index: {args.camera} | pause: {args.pause}s | resume: {args.resume}s")
    print("Leave this window open while OBS is running. Press Ctrl+C to stop.")
    server.serve_forever()


if __name__ == "__main__":
    main()
