import atexit
import fcntl
import io
import os
import signal
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
APP_FILE = PROJECT_DIR / "app.py"
HOST = "127.0.0.1"
PORT = 8501
LOG_DIR = Path.home() / ".cache" / "expense-app-desktop"
LOG_FILE = LOG_DIR / "launcher.log"
LOCK_FILE = LOG_DIR / "launcher.lock"
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
LOG_MAX_BYTES = 5 * 1024 * 1024
LOG_BACKUP_COUNT = 5
BROWSER_CANDIDATES = [
    ("google-chrome", "chromium_app"),
    ("google-chrome-stable", "chromium_app"),
    ("chromium-browser", "chromium_app"),
    ("chromium", "chromium_app"),
    ("brave-browser", "chromium_app"),
    ("microsoft-edge", "chromium_app"),
    ("firefox", "firefox_window"),
]


def _rotate_logs_if_needed() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not LOG_FILE.exists():
        return

    if LOG_FILE.stat().st_size < LOG_MAX_BYTES:
        return

    oldest_backup = LOG_FILE.with_name(f"{LOG_FILE.name}.{LOG_BACKUP_COUNT}")
    if oldest_backup.exists():
        oldest_backup.unlink()

    for index in range(LOG_BACKUP_COUNT - 1, 0, -1):
        src = LOG_FILE.with_name(f"{LOG_FILE.name}.{index}")
        dst = LOG_FILE.with_name(f"{LOG_FILE.name}.{index + 1}")
        if src.exists():
            src.rename(dst)

    LOG_FILE.rename(LOG_FILE.with_name(f"{LOG_FILE.name}.1"))


def _log(message: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as handle:
        handle.write(f"[{timestamp}] {message}\n")


def _acquire_single_instance_lock() -> io.TextIOWrapper | None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    lock_handle = LOCK_FILE.open("a+", encoding="utf-8")

    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lock_handle.close()
        return None

    lock_handle.seek(0)
    lock_handle.truncate()
    lock_handle.write(str(os.getpid()))
    lock_handle.flush()
    return lock_handle


def _release_single_instance_lock(lock_handle: io.TextIOWrapper | None) -> None:
    if lock_handle is None:
        return

    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)
    finally:
        lock_handle.close()


def _is_port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((host, port)) == 0


def _wait_for_server(
    host: str,
    port: int,
    process: subprocess.Popen,
    timeout: float = 30.0,
) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        if process.poll() is not None:
            return False
        if _is_port_open(host, port):
            return True
        time.sleep(0.2)
    return False


def _stop_process(process: subprocess.Popen | None) -> None:
    if process is None:
        return

    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def _launch_browser_window(url: str) -> subprocess.Popen | None:
    for browser_cmd, mode in BROWSER_CANDIDATES:
        resolved = shutil.which(browser_cmd)
        if not resolved:
            continue

        if mode == "chromium_app":
            args = [
                resolved,
                f"--app={url}",
                "--new-window",
                f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}",
            ]
        else:
            args = [
                resolved,
                "--new-window",
                f"--width={WINDOW_WIDTH}",
                f"--height={WINDOW_HEIGHT}",
                url,
            ]

        try:
            process = subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            _log(f"Opened browser window with {browser_cmd} (pid={process.pid})")
            return process
        except OSError:
            continue

    _log("No supported browser binary found; falling back to default webbrowser")
    webbrowser.open(url)
    return None


def main() -> int:
    _rotate_logs_if_needed()
    _log("Launcher started")

    lock_handle = _acquire_single_instance_lock()
    if lock_handle is None:
        _log("Another launcher instance is already running; exiting")
        print("Expense App is already running.")
        return 0

    _log("Acquired single-instance lock")

    try:
        if not APP_FILE.exists():
            _log(f"Could not find app entry file: {APP_FILE}")
            return 1

        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(APP_FILE),
            "--server.headless",
            "true",
            "--server.address",
            HOST,
            "--server.port",
            str(PORT),
            "--browser.gatherUsageStats",
            "false",
        ]

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as log_handle:
            log_handle.write(f"\n===== Session {datetime.now().isoformat()} =====\n")

            process = subprocess.Popen(
                cmd,
                cwd=str(PROJECT_DIR),
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            _log(f"Started Streamlit process (pid={process.pid})")

            atexit.register(_stop_process, process)

            def _handle_signal(signum, _frame):
                _log(f"Received signal {signum}; shutting down")
                _stop_process(process)
                sys.exit(0)

            signal.signal(signal.SIGINT, _handle_signal)
            signal.signal(signal.SIGTERM, _handle_signal)

            if not _wait_for_server(HOST, PORT, process):
                exit_code = process.poll()
                _log(f"Expense App failed to start in time (streamlit_exit={exit_code})")
                _stop_process(process)
                return 1

            url = f"http://{HOST}:{PORT}"
            _log(f"Server is reachable at {url}")
            browser_process = _launch_browser_window(url)

            try:
                if browser_process is None:
                    while process.poll() is None:
                        time.sleep(1)
                else:
                    browser_process.wait()
            finally:
                _log("Browser window closed; stopping Streamlit")
                _stop_process(browser_process)
                _stop_process(process)
                _log("Launcher exited cleanly")

        return 0
    finally:
        _release_single_instance_lock(lock_handle)


if __name__ == "__main__":
    os.chdir(PROJECT_DIR)
    raise SystemExit(main())
