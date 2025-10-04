from .config import CONFIG_DIR
import os, json

def _token_path(profile: str = 'default'):
    return CONFIG_DIR / f'token_{profile}.json'

def delete_token(profile: str = 'default'):
    try:
        p = _token_path(profile)
        if p.exists():
            p.unlink()
        return True
    except Exception:
        return False

def get_credentials(profile: str = 'default', force_reauth: bool = False):
    # Stub: retourne un dict vide simulant des credentials
    p = _token_path(profile)
    if force_reauth or not p.exists():
        with open(p, 'w', encoding='utf-8') as f:
            json.dump({'stub': True, 'profile': profile}, f)
    return {'stub': True, 'profile': profile}
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from .constants import SCOPES, CLIENT_SECRETS, TOKEN_FILE, TOKENS_DIR


def _resolve_token_path(profile: str | None) -> str:
    if profile:
        os.makedirs(TOKENS_DIR, exist_ok=True)
        safe = ''.join(c for c in profile if c.isalnum() or c in ('-', '_', '.')) or 'default'
        return os.path.join(TOKENS_DIR, f"{safe}.pickle")
    return TOKEN_FILE


def delete_token(profile: str | None = None):
    """Supprime le fichier de token pour forcer une ré-authentification."""
    token_path = _resolve_token_path(profile)
    try:
        if os.path.exists(token_path):
            os.remove(token_path)
    except Exception:
        pass


def get_credentials(profile: str = None, force_reauth: bool = False):
    if not os.path.exists(CLIENT_SECRETS):
        raise FileNotFoundError(f"Fichier client_secret.json manquant: {CLIENT_SECRETS}")

    # Déterminer le fichier token selon profil
    token_path = _resolve_token_path(profile)

    creds = None
    if (not force_reauth) and os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
        except Exception:
            # Échec du refresh (ex: invalid_grant) → on force un nouveau flow
            creds = None
    if force_reauth or (not creds) or (not creds.valid):
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
        # Désactive l'ouverture auto du navigateur si aucun display (ex: serveur, WSL) ou si T2Y_NO_BROWSER défini
        display_available = bool(os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY'))
        open_browser = display_available and not bool(os.environ.get('T2Y_NO_BROWSER'))
        try:
            creds = flow.run_local_server(port=0, open_browser=open_browser)
        except Exception:
            # Fallback console: affiche l'URL et demande le code de vérification
            creds = flow.run_console()
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)

    # Build service; proxy peut être géré via variables d'env (HTTP_PROXY/HTTPS_PROXY)
    return build('youtube', 'v3', credentials=creds)
