import os
import sys
import json
import random
import subprocess
import platform
import threading
from pathlib import Path
import subprocess
import sys



# -----------------------------------------------
# BASE PATHS
# -----------------------------------------------
BASE_DIR = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
LOGS_DIR = BASE_DIR / "scripts" / "Logs"
STATE_FILE = BASE_DIR / "buffer.json"
TRIGGER_FILE = BASE_DIR / "trigger.txt"

# ensure Logs dir always exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------
# PHRASE GROUPS
# -----------------------------------------------
PHRASE_GROUPS = [
    {
        "name": "ClearPicture",
        "phrases": ["clear picture", "full picture", "complete picture"]
    },
    {
        "name": "SmokingGun",
        "phrases": ["smoking gun"]
    },
    {
        "name": "Caveat",
        "phrases": ["caveat"]
    },
    {
        "name": "Nuance",
        "phrases": ["it's nuanced", "it's more nuanced", "nuance here"]
    }
]

# -----------------------------------------------
# LOAD BUFFER STATE
# -----------------------------------------------
try:
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        buffer = json.load(f)
except Exception:
    buffer = {}

# -----------------------------------------------
# HELPERS
# -----------------------------------------------
def normalize(text):
    return (text or "").lower()

def check_match(text):
    for group in PHRASE_GROUPS:
        if any(phrase in text for phrase in group["phrases"]):
            return group["name"]
    return None

def write_log(filename, content):
    try:
        with open(LOGS_DIR / filename, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception:
        pass

def play_audio(sound_path):
    """Play audio non-blocking, platform specific."""
    if not sound_path or not sound_path.exists():
        return

    system = platform.system()

    def _play():
        try:
            if system == "Windows":
                import winsound
                winsound.PlaySound(str(sound_path), winsound.SND_FILENAME)
            elif system == "Darwin":
                subprocess.Popen(["afplay", str(sound_path)])
            else:
                subprocess.Popen(["aplay", str(sound_path)])
        except Exception as e:
            write_log("audio_error.txt", str(e))

    threading.Thread(target=_play, daemon=True).start()

def show_media(image_path, sound_path):
    """Show transparent tkinter window with image and play audio - all platforms."""
    try:
        import tkinter as tk
        from PIL import Image, ImageTk

        # play audio first, non-blocking
        play_audio(sound_path)

        root = tk.Tk()
        root.overrideredirect(True)   # no title bar or border
        root.attributes("-topmost", True)
        root.configure(bg="yellow")

        # transparency key - yellow background becomes transparent
        system = platform.system()
        if system == "Windows":
            root.wm_attributes("-transparentcolor", "yellow")
        elif system == "Darwin":
            root.attributes("-transparent", True)
            root.wm_attributes("-transparentcolor", "yellow")
        else:
            # Linux - transparency depends on compositor, best effort
            root.wm_attributes("-transparentcolor", "yellow")

        img = Image.open(str(image_path))
        photo = ImageTk.PhotoImage(img)

        # center on screen
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = (sw - img.width) // 2
        y = (sh - img.height) // 2
        root.geometry(f"{img.width}x{img.height}+{x}+{y}")

        label = tk.Label(root, image=photo, bg="yellow", borderwidth=0)
        label.pack()

        # close after 3 seconds
        root.after(3000, root.destroy)
        root.mainloop()

    except ImportError as e:
        write_log("tkinter_error.txt", f"Missing dependency: {e}\nRun: pip install pillow")
    except Exception as e:
        write_log("tkinter_error.txt", str(e))

# -----------------------------------------------
# MAIN - READ STDIN
# -----------------------------------------------
def main():
    raw = sys.stdin.read()

    try:
        payload = json.loads(raw) if raw else {}

        msg_id = payload.get("message_id")
        delta = payload.get("delta", "")

        if not msg_id:
            return

        if msg_id not in buffer:
            buffer[msg_id] = {"text": "", "fired": False}

        buffer[msg_id]["text"] += delta

        full_text = normalize(buffer[msg_id]["text"])

        matched_group = check_match(full_text)

        if not buffer[msg_id]["fired"] and matched_group:
            buffer[msg_id]["fired"] = True

            # write trigger file
            with open(TRIGGER_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "trigger": matched_group,
                    "message_id": msg_id,
                    "text": full_text,
                    "time": __import__("datetime").datetime.now().isoformat()
                }, f, indent=2)

            # resolve media dir
            media_dir = BASE_DIR / "hooks" / "Resources" / matched_group

            image_path = None
            sound_path = None

            # pick random image
            try:
                images = [f for f in media_dir.iterdir()
                          if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
                if images:
                    image_path = random.choice(images)
            except Exception as e:
                write_log("image_error.txt", str(e))

            # pick random sound
            try:
                sounds = [f for f in media_dir.iterdir()
                          if f.suffix.lower() == ".wav"]
                if sounds:
                    sound_path = random.choice(sounds)
            except Exception as e:
                write_log("sound_error.txt", str(e))

            # write debug log
            write_log("debug_render.json", json.dumps({
                "media_dir": str(media_dir),
                "image_path": str(image_path),
                "sound_path": str(sound_path),
                "media_dir_exists": media_dir.exists()
            }, indent=2))

            # launch GUI if we have an image
            if image_path and image_path.exists():
                show_media(image_path, sound_path)

    except Exception as e:
        write_log("error.txt", str(e))

    finally:
        # persist buffer always
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(buffer, f, indent=2)
        except Exception as e:
            write_log("buffer_error.txt", str(e))

if __name__ == "__main__":
    main()