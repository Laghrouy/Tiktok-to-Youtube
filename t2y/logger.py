from .config import LOG_FILE
from datetime import datetime

def log(level: str, message: str):
    try:
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] {level.upper()}: {message}\n")
    except Exception:
        pass
