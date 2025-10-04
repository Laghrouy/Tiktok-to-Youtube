from datetime import datetime

def parse_rfc3339(s: str):
    try:
        return datetime.fromisoformat(s.replace('Z','+00:00'))
    except Exception:
        return None
