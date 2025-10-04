from pathlib import Path

HOME = Path.home()
CONFIG_DIR = HOME / ".config" / "tiktok-to-youtube"
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = CONFIG_DIR / 't2y.log'
SETTINGS_FILE = CONFIG_DIR / 'settings.json'
