from pathlib import Path
from .config import CONFIG_DIR

YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "17": "Sports",
    "20": "Gaming",
    "22": "People & Blogs",
}

LANGUAGES = {
    "en": "English",
    "fr": "Français",
}

LICENSES = {
    "youtube": "Standard YouTube License",
    "creativeCommon": "Creative Commons",
}

PROFILES_FILE = CONFIG_DIR / 'profiles.json'
WATCH_STATE_FILE = CONFIG_DIR / 'watch_state.json'
UPLOADS_DB = CONFIG_DIR / 'uploads_db.json'
import os
from pathlib import Path

# Étendre les scopes pour couvrir l'upload et les mises à jour (recordingDetails, playlists)
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: BASE_DIR here is the package dir; client_secret/token live one level up (repo script dir)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
TOKEN_FILE = os.path.join(PROJECT_DIR, "token.pickle")
CLIENT_SECRETS = os.path.join(PROJECT_DIR, "client_secret.json")

DEFAULT_CATEGORY_ID = "22"
DEFAULT_TAGS = ["tiktok"]

YOUTUBE_CATEGORIES = {
    "Film & Animation": "1",
    "Autos & Vehicles": "2",
    "Music": "10",
    "Pets & Animals": "15",
    "Sports": "17",
    "Travel & Events": "19",
    "Gaming": "20",
    "People & Blogs": "22",
    "Comedy": "23",
    "Entertainment": "24",
    "News & Politics": "25",
    "Howto & Style": "26",
    "Education": "27",
    "Science & Technology": "28",
}

LANGUAGES = {
    "Français (fr)": "fr",
    "English (en)": "en",
    "Español (es)": "es",
    "Deutsch (de)": "de",
    "العربية (ar)": "ar",
    "Português (pt)": "pt",
    "Italiano (it)": "it",
}

LICENSES = {
    "Standard YouTube": "youtube",
    "Creative Commons": "creativeCommon",
}

CONFIG_DIR = Path.home() / ".config" / "tiktok-to-youtube"
LOG_FILE = CONFIG_DIR / "app.log"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
TOKENS_DIR = CONFIG_DIR / "tokens"
PROFILES_FILE = CONFIG_DIR / "profiles.json"
WATCH_STATE_FILE = CONFIG_DIR / "watch.json"
UPLOADS_DB = CONFIG_DIR / "uploads.json"
