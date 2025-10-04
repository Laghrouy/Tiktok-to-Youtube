import time

def upload_to_youtube(filepath: str, title: str, description: str, privacy: str, on_progress=None, advanced: dict | None = None):
    for p in (5, 20, 50, 80, 100):
        time.sleep(0.05)
        if on_progress:
            try:
                on_progress(p)
            except Exception:
                pass
    return 'video_stub_id'

def apply_post_upload_settings(creds, video_id: str, adv: dict):
    # Stub: ne fait rien
    return True
import time
import random
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .auth import get_credentials, delete_token
from .constants import DEFAULT_CATEGORY_ID
from .logger import log


def upload_to_youtube(video_path, title, description, privacy, on_progress=None, advanced=None):
    adv = advanced or {}
    profile = (adv.get('profile') if isinstance(adv, dict) else None) if adv else None
    
    # Préparer timeout et proxy avant de construire le client
    timeout = adv.get('timeout') or 60
    try:
        timeout = float(timeout)
    except Exception:
        timeout = 60.0
    # Proxy support via env si fourni
    proxy = (adv.get('proxy') or '').strip()
    if proxy:
        import os
        os.environ['HTTPS_PROXY'] = proxy
        os.environ['HTTP_PROXY'] = proxy

    # Obtenir le client YouTube (peut déclencher le flow OAuth si aucun token)
    youtube = get_credentials(profile)
    # Régler le timeout sur la session HTTP autorisée du client
    try:
        if hasattr(youtube, '_http') and youtube._http is not None:
            # httplib2.Http / AuthorizedHttp supporte l'attribut timeout
            setattr(youtube._http, 'timeout', timeout)
    except Exception:
        pass

    category_id = adv.get("categoryId") or DEFAULT_CATEGORY_ID
    default_lang = adv.get("defaultLanguage")
    made_for_kids = adv.get("madeForKids")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
        },
    }
    if default_lang:
        body["snippet"]["defaultLanguage"] = default_lang
    if made_for_kids is not None:
        body["status"]["madeForKids"] = bool(made_for_kids)

    if adv.get("tags"):
        body["snippet"]["tags"] = adv["tags"]
    if adv.get("license"):
        body["status"]["license"] = adv["license"]
    if adv.get("selfDeclaredMadeForKids") is not None:
        body["status"]["selfDeclaredMadeForKids"] = bool(adv["selfDeclaredMadeForKids"])
    if adv.get("publishAt"):
        body["status"]["publishAt"] = adv["publishAt"]
        body["status"]["privacyStatus"] = "private"
    if adv.get("embeddable") is not None:
        body["status"]["embeddable"] = bool(adv["embeddable"])
    if adv.get("license"):
        body["status"]["license"] = adv["license"]

    # chunksize configurable (MB) — arrondi au multiple de 256KB requis par l’API
    chunk_mb = adv.get('uploadChunkMB') or 8
    try:
        chunk_mb = float(chunk_mb)
    except Exception:
        chunk_mb = 8.0
    # borne minimale 1MB
    if chunk_mb <= 0:
        chunk_mb = 1.0
    chunk_size = int(chunk_mb * 1024 * 1024)
    # arrondi à un multiple de 256KB
    base = 256 * 1024
    if chunk_size % base != 0:
        chunk_size = max(base, (chunk_size // base) * base)
    media_body = MediaFileUpload(video_path, chunksize=chunk_size, resumable=True)

    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media_body)

    # Retries avec backoff exponentiel et jitter pour 429 / 5xx
    try:
        max_retries = int(adv.get('uploadMaxRetries') or 8)
    except Exception:
        max_retries = 8
    attempt = 0
    response = None
    force_reauth_done = False
    while response is None:
        try:
            # Utiliser l'HTTP autorisé interne du client (avec credentials)
            status, response = request.next_chunk()
            if status and on_progress:
                on_progress(status.progress() * 100.0)
        except HttpError as e:
            code = getattr(e, 'status_code', None) or getattr(getattr(e, 'resp', None), 'status', None)
            # Si non authentifié (401), on supprime le token et on relance une seule fois l'OAuth
            if code == 401 and not force_reauth_done:
                try:
                    delete_token(profile)
                except Exception:
                    pass
                # Recréer le client en forçant l'auth
                youtube = get_credentials(profile, force_reauth=True)
                try:
                    if hasattr(youtube, '_http') and youtube._http is not None:
                        setattr(youtube._http, 'timeout', timeout)
                except Exception:
                    pass
                request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media_body)
                force_reauth_done = True
                continue
            if code in (429, 500, 502, 503, 504) and attempt < max_retries:
                # backoff
                sleep_s = min(60, (2 ** attempt)) * (0.5 + random.random())
                log('error', f"Upload chunk erreur {code}, retry dans {sleep_s:.1f}s (tentative {attempt+1}/{max_retries})")
                time.sleep(sleep_s)
                attempt += 1
                continue
            raise
        except Exception as e:
            if attempt < max_retries:
                sleep_s = min(60, (2 ** attempt)) * (0.5 + random.random())
                log('error', f"Upload chunk échec: {e} — retry dans {sleep_s:.1f}s (tentative {attempt+1}/{max_retries})")
                time.sleep(sleep_s)
                attempt += 1
                continue
            raise
    video_id = response.get("id")
    log('info', f"Upload terminé. Video ID: {video_id}")
    return video_id


def apply_post_upload_settings(youtube, video_id, advanced):
    if not advanced:
        return
    log('info', 'Application des paramètres avancés (recordingDetails / playlists)')

    loc_desc = advanced.get("locationDescription")
    lat = advanced.get("latitude")
    lon = advanced.get("longitude")
    rec_date = advanced.get("recordingDate")

    if any([loc_desc, lat, lon, rec_date]):
        body = {"id": video_id, "recordingDetails": {}}
        if loc_desc:
            body["recordingDetails"]["locationDescription"] = loc_desc
        if lat and lon:
            try:
                body["recordingDetails"]["location"] = {"latitude": float(lat), "longitude": float(lon)}
            except Exception:
                pass
        if rec_date:
            body["recordingDetails"]["recordingDate"] = rec_date
        try:
            youtube.videos().update(part="recordingDetails", body=body).execute()
            log('info', 'recordingDetails mis à jour')
        except Exception as e:
            log('error', f"Échec update recordingDetails: {e}")

    playlists = advanced.get("playlists") or []
    for pid in playlists:
        try:
            youtube.playlistItems().insert(part="snippet", body={
                "snippet": {
                    "playlistId": pid,
                    "resourceId": {"kind": "youtube#video", "videoId": video_id}
                }
            }).execute()
            log('info', f"Ajouté à la playlist {pid}")
        except Exception as e:
            log('error', f"Échec ajout playlist {pid}: {e}")
