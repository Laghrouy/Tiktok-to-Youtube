"""
Gestion (stub) de l'auth TikTok côté local.
Ce module n'appelle pas l'API TikTok: il sert à préparer l'intégration
et stocker un jeton factice pour valider les flux dans l'app.
"""
from __future__ import annotations
from typing import Optional, Tuple
import json, os, time, secrets, urllib.parse, base64, hashlib
from .constants import CONFIG_DIR

_TT_FILE = CONFIG_DIR / 'tiktok_token.json'

AUTH_URL = 'https://www.tiktok.com/v2/auth/authorize/'
TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/'

def _get_client_config() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    cid = os.environ.get('TIKTOK_CLIENT_KEY') or os.environ.get('TIKTOK_CLIENT_ID')
    csec = os.environ.get('TIKTOK_CLIENT_SECRET')
    redirect = os.environ.get('TIKTOK_REDIRECT_URI')
    return cid, csec, redirect

def is_configured() -> bool:
    cid, csec, _ = _get_client_config()
    return bool(cid and csec)

def is_connected() -> bool:
    try:
        return os.path.exists(_TT_FILE)
    except Exception:
        return False

def get_status() -> dict:
    try:
        d = {'connected': False, 'configured': is_configured()}
        if os.path.exists(_TT_FILE):
            with open(_TT_FILE, 'r', encoding='utf-8') as f:
                t = json.load(f)
            d.update({'connected': True, 'profile': t.get('profile') or 'default'})
        return d
    except Exception:
        return {'connected': False, 'configured': is_configured()}

def start_auth(profile: Optional[str] = None, redirect_uri: Optional[str] = None, scope: Optional[str] = None) -> dict:
    """Construit l'URL d'autorisation TikTok v2 si configuré. Sinon, retourne une URL factice."""
    client_key, _, env_redirect = _get_client_config()
    redir = redirect_uri or env_redirect or 'http://localhost:8000/api/tiktok/callback'
    scope = scope or 'user.info.basic,video.upload'
    state = secrets.token_urlsafe(16)
    # Générer code_verifier et code_challenge (PKCE)
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).rstrip(b'=').decode('utf-8')
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode('utf-8')).digest()).rstrip(b'=').decode('utf-8')
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_DIR / 'tiktok_oauth_state.json', 'w', encoding='utf-8') as f:
            json.dump({'state': state, 'profile': profile or 'default', 'ts': int(time.time()), 'code_verifier': code_verifier}, f)
    except Exception:
        pass
    if client_key:
        params = {
            'client_key': client_key,
            'response_type': 'code',
            'scope': scope,
            'redirect_uri': redir,
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }
        url = AUTH_URL + '?' + urllib.parse.urlencode(params)
    else:
        url = 'https://www.tiktok.com/auth/start?missing_env=1'
    return {'ok': True, 'authUrl': url, 'profile': profile or 'default'}

def exchange_code(code: str, profile: Optional[str] = None, redirect_uri: Optional[str] = None) -> dict:
    """Échange le code contre des tokens si configuré. Stocke localement les tokens ou, si non configuré, un token factice."""
    cid, csec, env_redirect = _get_client_config()
    redir = redirect_uri or env_redirect or 'http://localhost:8000/api/tiktok/callback'
    # Charger le code_verifier sauvegardé lors du start_auth
    code_verifier = None
    try:
        with open(CONFIG_DIR / 'tiktok_oauth_state.json', 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            code_verifier = state_data.get('code_verifier')
    except Exception:
        pass
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if cid and csec and code_verifier:
            data = {
                'client_key': cid,
                'client_secret': csec,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': redir,
                'code_verifier': code_verifier,
            }
            try:
                import requests  # type: ignore
                r = requests.post(TOKEN_URL, json=data, timeout=10)
                if r.status_code >= 400:
                    return {'ok': False, 'error': f'token http {r.status_code}: {r.text[:200] if r.text else ""}'}
                tok = r.json()
            except Exception as e:
                return {'ok': False, 'error': f'token request failed: {e}'}
            with open(_TT_FILE, 'w', encoding='utf-8') as f:
                json.dump({
                    'access_token': tok.get('access_token'),
                    'refresh_token': tok.get('refresh_token'),
                    'expires_in': tok.get('expires_in'),
                    'scope': tok.get('scope'),
                    'obtained_at': int(time.time()),
                    'profile': profile or 'default'
                }, f, ensure_ascii=False, indent=2)
            return {'ok': True}
        else:
            # fallback: token factice local si non configuré
            with open(_TT_FILE, 'w', encoding='utf-8') as f:
                json.dump({'token': f'fake_token_for_{code}', 'profile': profile or 'default'}, f, ensure_ascii=False, indent=2)
            return {'ok': True, 'fake': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}

def get_token() -> Optional[dict]:
    try:
        if os.path.exists(_TT_FILE):
            with open(_TT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None

def disconnect() -> dict:
    try:
        if os.path.exists(_TT_FILE):
            os.remove(_TT_FILE)
        return {'ok': True}
    except Exception as e:
        return {'ok': False, 'error': str(e)}
