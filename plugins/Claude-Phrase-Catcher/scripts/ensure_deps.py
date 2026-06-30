import subprocess
import sys
import os
from pathlib import Path

BASE_DIR = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", "."))
LOGS_DIR = BASE_DIR / "scripts" / "Logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def log(msg):
    with open(LOGS_DIR / "deps_install.log", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def ensure_pillow():
    try:
        import PIL  # noqa
        log("Pillow already installed.")
    except ImportError:
        log("Pillow not found, attempting install...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "pillow"],
                capture_output=True,
                text=True
            )
            log(f"pip exit code: {result.returncode}")
            log(f"pip stdout: {result.stdout}")
            log(f"pip stderr: {result.stderr}")
        except Exception as e:
            log(f"pip install raised exception: {e}")

if __name__ == "__main__":
    ensure_pillow()