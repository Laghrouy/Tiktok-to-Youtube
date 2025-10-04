# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv()
# Création de l'application FastAPI (doit être défini avant toute utilisation de 'app')
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
app = FastAPI()
# --- Upload TikTok vidéo ---
@app.post('/api/tiktok/upload')
async def api_tiktok_upload(request: Request, file: UploadFile = File(...), caption: str = Form(...)):
    try:
        # Sauver le fichier temporairement
        import tempfile, os
        suffix = os.path.splitext(file.filename)[1] if file.filename else '.mp4'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        # Upload TikTok via t2y.tiktok_poster
        from t2y.tiktok_poster import post_to_tiktok
        tt_id = post_to_tiktok(tmp_path, caption=caption)
        # Nettoyer le fichier temporaire
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        return {"ok": True, "id": tt_id}
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=500)


@app.get("/youtube", response_class=HTMLResponse)
async def youtube_page(request: Request):
    ctx = {
        "request": request,
        "q": state.queue,
        "queue": {
            "running": state.queue_running,
            "paused": state.queue_paused
        },
        # Listes pour les selects UI
        "categories": list(YOUTUBE_CATEGORIES.items()),
        "languages": list(LANGUAGES.items()),
        "licenses": list(LICENSES.items()),
    }
    html = templates.get_template("youtube.html").render(ctx)
    return HTMLResponse(content=html)

@app.get("/tiktok", response_class=HTMLResponse)
async def tiktok_page(request: Request):
    ctx = {
        "request": request,
        "q": state.queue,
        "queue": {
            "running": state.queue_running,
            "paused": state.queue_paused
        },
        # Pour TikTok, pas de catégories/langues/licences YouTube
    }
    html = templates.get_template("tiktok.html").render(ctx)
    return HTMLResponse(content=html)
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, FileResponse, Response
from fastapi import UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .state import state
from t2y.constants import YOUTUBE_CATEGORIES, LANGUAGES, LICENSES, PROFILES_FILE
from t2y.config import LOG_FILE
from t2y.config import SETTINGS_FILE, CONFIG_DIR
from t2y.auth import delete_token as auth_delete_token, get_credentials as auth_get_credentials
from t2y.tiktok_auth import is_connected as tt_is_connected, get_status as tt_get_status, start_auth as tt_start_auth, exchange_code as tt_exchange_code, disconnect as tt_disconnect
import json, shutil, subprocess, zipfile, io, os
import time



# Static dir (for favicon or assets)
try:
    app.mount("/static", StaticFiles(directory="webapp/static"), name="static")
except Exception:
    pass

# User uploads (for watermark previews)
try:
    uploads_dir = str(CONFIG_DIR / 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    app.mount("/user-uploads", StaticFiles(directory=uploads_dir), name="user-uploads")
except Exception:
    pass

templates = Jinja2Templates(directory="webapp/templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Rendu Jinja immédiat (évite le streaming qui peut produire un body vide dans certains contextes)
    ctx = {
        "request": request,
        "q": state.queue,
        "watch": {
            "running": state.watch_running,
            "handle": state.handle,
            "interval": state.interval_min,
            "quota": state.quota,
            "inc_kw": state.inc_kw,
            "exc_kw": state.exc_kw,
            "min_dur": state.min_dur,
            "max_dur": state.max_dur,
            "last_poll": state.last_poll,
        },
        "queue": {
            "running": state.queue_running,
            "paused": state.queue_paused
        },
        # Listes pour les selects UI
        "categories": list(YOUTUBE_CATEGORIES.items()),
        "languages": list(LANGUAGES.items()),
        "licenses": list(LICENSES.items()),
    }
    html = templates.get_template("index.html").render(ctx)
    return HTMLResponse(content=html)

@app.get('/api/tiktok/status')
async def api_tiktok_status():
    try:
        return {'ok': True, **tt_get_status()}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/tiktok/connect')
async def api_tiktok_connect(request: Request):
    try:
        b = await request.json()
        profile = (b.get('profile') or 'default') if isinstance(b, dict) else 'default'
        # Construire redirect_uri depuis la requête
        base = str(request.base_url).rstrip('/')
        redir = base + '/api/tiktok/callback'
        return tt_start_auth(profile, redirect_uri=redir)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/tiktok/callback')
async def api_tiktok_callback(request: Request, code: str = ''):
    try:
        if not code:
            return JSONResponse({'error': 'code manquant'}, status_code=400)
        base = str(request.base_url).rstrip('/')
        redir = base + '/api/tiktok/callback'
        r = tt_exchange_code(code, redirect_uri=redir)
        if not r.get('ok'):
            return JSONResponse({'error': r.get('error','exchange failed')}, status_code=500)
        return RedirectResponse('/')
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/tiktok/disconnect')
async def api_tiktok_disconnect():
    try:
        return tt_disconnect()
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/status')
async def api_status():
    return {
        'watch': {
            'running': state.watch_running,
            'handle': state.handle,
            'interval': state.interval_min,
            'quota': state.quota,
            'inc_kw': state.inc_kw,
            'exc_kw': state.exc_kw,
            'min_dur': state.min_dur,
            'max_dur': state.max_dur,
            'last_poll': state.last_poll,
        },
        'queue': {
            'running': state.queue_running,
            'paused': state.queue_paused,
            'size': len(state.queue),
            'lastVideoId': state.last_video_id,
            'items': [
                {
                    'iid': it.get('iid',''),
                    'url': it.get('url',''),
                    'title': it.get('title',''),
                    'status': it.get('status',''),
                    'badges': it.get('badges', []),
                    'd_pct': it.get('d_pct', 0),
                    'u_pct': it.get('u_pct', 0),
                    'result': it.get('result',''),
                    'results': it.get('results', {})
                }
                for it in list(state.queue)
            ]
        }
    }

@app.post('/api/watch/start')
async def api_watch_start(request: Request):
    body = await request.json()
    handle = (body.get('handle') or '').strip()
    interval = float(body.get('interval') or 10)
    quota = int(body.get('quota') or 0)
    # Filtres
    def _to_list(v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        return [t.strip() for t in str(v).split(',') if t.strip()]
    inc_kw = _to_list(body.get('inc_kw'))
    exc_kw = _to_list(body.get('exc_kw'))
    min_dur = int(body.get('min_dur') or 0)
    max_dur = int(body.get('max_dur') or 0)
    state.start_watch(handle, interval, quota, inc_kw=inc_kw, exc_kw=exc_kw, min_dur=min_dur, max_dur=max_dur)
    return {'ok': True}

@app.post('/api/watch/stop')
async def api_watch_stop():
    state.stop_watch()
    return {'ok': True}

@app.post('/api/queue/add')
async def api_queue_add(request: Request):
    b = await request.json()
    # Normaliser tags/playlists
    def _to_list(v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v)
        return [t.strip() for t in s.split(',') if t.strip()]
    def _sanitize_tags_500(tags_list):
        try:
            if not tags_list:
                return tags_list
            cleaned = []
            seen = set()
            total = 0
            for t in tags_list:
                s = (t or '').strip().lstrip('#')
                if not s:
                    continue
                key = s.lower()
                if key in seen:
                    continue
                if total + len(s) > 500:
                    continue
                cleaned.append(s)
                seen.add(key)
                total += len(s)
            return cleaned
        except Exception:
            return tags_list
    tags = _sanitize_tags_500(_to_list(b.get('tags')))
    playlists = _to_list(b.get('playlists'))
    adv = {
        'tags': tags,
        'categoryId': b.get('categoryId') or None,
        'defaultLanguage': b.get('defaultLanguage') or None,
        'madeForKids': bool(b.get('madeForKids')),
        'license': b.get('license') or None,
        'draft': bool(b.get('draft')),
        'publishAt': b.get('publishAt') or None,
        'recordingDate': b.get('recordingDate') or None,
        'locationDescription': b.get('locationDescription') or None,
        'latitude': b.get('latitude') or None,
        'longitude': b.get('longitude') or None,
        'playlists': playlists,
        'timeout': (b.get('timeout') or '').strip(),
        'proxy': (b.get('proxy') or '').strip(),
        'uploadChunkMB': (b.get('uploadChunkMB') or '').strip(),
        'uploadMaxRetries': (b.get('uploadMaxRetries') or '').strip(),
        'profile': (b.get('profile') or '').strip() or None,
        # ffmpeg options
        'ff_mode': (b.get('ff_mode') or 'none').strip(),
        'ff_target_w': b.get('ff_target_w') or None,
        'ff_target_h': b.get('ff_target_h') or None,
        'ff_normalize': bool(b.get('ff_normalize')),
        'ff_remux': bool(b.get('ff_remux')),
        'ff_trim_start': b.get('ff_trim_start') or None,
        'ff_trim_end': b.get('ff_trim_end') or None,
        'ff_wm_path': (b.get('ff_wm_path') or '').strip(),
        'ff_wm_pos': (b.get('ff_wm_pos') or 'bottom-right').strip(),
        'ff_force_916': bool(b.get('ff_force_916')),
    }
    # destinations demandées
    adv['destinations'] = {
        'yt': bool(b.get('dest_yt', True)),
        'ig': bool(b.get('dest_ig', False)),
        'tt': bool(b.get('dest_tt', False)),
    }
    it = state.queue_add(
        b.get('url') or '',
        b.get('title') or '',
        b.get('description') or '',
        adv=adv,
        privacy=(b.get('privacy') or 'private').strip() or 'private',
    )
    return {'ok': True, 'item': it}

@app.post('/api/queue/start')
async def api_queue_start():
    state.start_queue()
    return {'ok': True}

@app.post('/api/queue/pause')
async def api_queue_pause(request: Request):
    b = await request.json()
    state.pause_queue(bool(b.get('pause')))
    return {'ok': True}

@app.post('/api/queue/stop')
async def api_queue_stop():
    state.stop_queue()
    return {'ok': True}

@app.post('/api/queue/move')
async def api_queue_move(request: Request):
    b = await request.json()
    iid = (b.get('iid') or '').strip()
    direction = (b.get('direction') or '').strip()
    if not iid or direction not in ('up','down'):
        return JSONResponse({'error': 'params invalides'}, status_code=400)
    ok = state.move_item(iid, direction)
    return {'ok': bool(ok)}

@app.post('/api/queue/pause_after_n')
async def api_queue_pause_after_n(request: Request):
    b = await request.json()
    try:
        state.pause_after_n_enabled = bool(b.get('enabled'))
        state.pause_after_n_value = int(b.get('value') or 0)
        return {'ok': True}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=400)

@app.post('/api/prefill')
async def api_prefill(request: Request):
    from t2y.metadata import fetch_tiktok_metadata
    b = await request.json()
    url = (b.get('url') or '').strip()
    if not url:
        return JSONResponse({'error': 'url manquante'}, status_code=400)
    try:
        meta = fetch_tiktok_metadata(url) or {}
        return {'ok': True, 'meta': meta}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/queue/clear_done')
async def api_queue_clear_done():
    n = state.clear_done()
    return {'ok': True, 'removed': n}

@app.post('/api/queue/resume_errors')
async def api_queue_resume_errors():
    n = state.resume_errors()
    return {'ok': True, 'changed': n}

@app.post('/api/queue/remove')
async def api_queue_remove(request: Request):
    b = await request.json()
    iid = (b.get('iid') or '').strip()
    if not iid:
        return JSONResponse({'error': 'iid manquant'}, status_code=400)
    ok = state.remove_item(iid)
    return {'ok': bool(ok)}

@app.get('/api/logs')
async def api_logs(limit: int = 200):
    try:
        p = str(LOG_FILE)
        if not os.path.exists(p):
            return {'ok': True, 'lines': []}
        lines = []
        with open(p, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()[-int(max(10, min(limit, 2000))):]
        return {
            'ok': True,
            'lines': lines,
        }
    except Exception as e:
        # Tolérer les erreurs de lecture et retourner une liste vide
        return {'ok': True, 'lines': []}

@app.get('/api/settings')
async def api_get_settings():
    try:
        d = {}
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            d = {}
        # Nous ne renvoyons qu’un sous-ensemble pertinent pour le web
        subset = {
            'defaultPrivacy': d.get('privacy') or 'private',
            'defaultProfile': d.get('profile') or 'default',
            'defaultTimeout': d.get('timeout') or d.get('timeoutUpload') or '',
            'defaultProxy': d.get('proxy') or '',
            'defaultChunkMB': d.get('uploadChunkMB') or '8',
            'defaultRetries': d.get('uploadMaxRetries') or '8',
        }
        return {'ok': True, 'settings': subset}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/css/health')
async def api_css_health():
    try:
        # Chemin du fichier CSS compilé attendu
        css_path = os.path.join('webapp', 'static', 'build', 'app.css')
        exists = os.path.exists(css_path)
        size = os.path.getsize(css_path) if exists else 0
        mtime = os.path.getmtime(css_path) if exists else 0
        # Heuristique: si très petit (< 4KB), probable fallback; si > 20KB, probable build Tailwind
        looks_fallback = exists and size > 0 and size < 4 * 1024
        compiled_ok = exists and size >= 20 * 1024
        # Contenu optionnel: vérifier présence de directives @tailwind compilées (devrait être absentes) ou classes générées
        sample = ''
        try:
            if exists:
                with open(css_path, 'r', encoding='utf-8', errors='ignore') as f:
                    sample = f.read(2048)
        except Exception:
            sample = ''
        return {
            'ok': True,
            'exists': bool(exists),
            'path': css_path,
            'size': int(size),
            'mtime': int(mtime),
            'compiledOk': bool(compiled_ok),
            'looksFallback': bool(looks_fallback),
            'sampleHead': sample[:200]
        }
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/settings')
async def api_set_settings(request: Request):
    b = await request.json()
    try:
        d = {}
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            d = {}
        d['privacy'] = (b.get('defaultPrivacy') or 'private')
        d['profile'] = (b.get('defaultProfile') or 'default')
        d['timeout'] = (b.get('defaultTimeout') or '')
        d['proxy'] = (b.get('defaultProxy') or '')
        d['uploadChunkMB'] = (b.get('defaultChunkMB') or '8')
        d['uploadMaxRetries'] = (b.get('defaultRetries') or '8')
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        return {'ok': True}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/ffmpeg/status')
async def api_ffmpeg_status():
    try:
        exe = shutil.which('ffmpeg')
        if not exe:
            return {'ok': True, 'found': False, 'path': None, 'version': ''}
        try:
            r = subprocess.run([exe, '-version'], capture_output=True, text=True, timeout=3)
            ver = (r.stdout or r.stderr or '').splitlines()[0] if (r.stdout or r.stderr) else ''
        except Exception:
            ver = ''
        return {'ok': True, 'found': True, 'path': exe, 'version': ver}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.get('/api/diagnostics')
async def api_diagnostics():
    try:
        from datetime import datetime
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        name = f't2y_diagnostics_{ts}.zip'
        outp = CONFIG_DIR / name
        with zipfile.ZipFile(outp, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            # logs & settings
            def _safe_add(path, arcname):
                try:
                    if path and os.path.exists(path):
                        z.write(path, arcname)
                except Exception:
                    pass
            _safe_add(str(LOG_FILE), 'logs/t2y.log')
            _safe_add(str(SETTINGS_FILE), 'config/settings.json')
            try:
                from t2y.constants import PROFILES_FILE, WATCH_STATE_FILE, UPLOADS_DB
                _safe_add(str(PROFILES_FILE), 'config/profiles.json')
                _safe_add(str(WATCH_STATE_FILE), 'config/watch_state.json')
                _safe_add(str(UPLOADS_DB), 'config/uploads_db.json')
            except Exception:
                pass
            try:
                qf = CONFIG_DIR / 'queue.json'
                _safe_add(str(qf), 'config/queue.json')
            except Exception:
                pass
            try:
                req = os.path.join(os.path.dirname(__file__), '..', 'requirements.txt')
                _safe_add(os.path.abspath(req), 'project/requirements.txt')
            except Exception:
                pass
        return FileResponse(str(outp), filename=name)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/profile/disconnect')
async def api_profile_disconnect(request: Request):
    b = await request.json()
    name = (b.get('profile') or 'default').strip() or 'default'
    try:
        auth_delete_token(name)
        return {'ok': True}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

@app.post('/api/profile/reauth')
async def api_profile_reauth(request: Request):
    import threading
    b = await request.json()
    name = (b.get('profile') or 'default').strip() or 'default'
    def _reauth():
        try:
            auth_get_credentials(name, force_reauth=True)
        except Exception:
            pass
    threading.Thread(target=_reauth, daemon=True).start()
    return {'ok': True}

@app.get('/api/net/test')
async def api_net_test(proxy: str = None, timeout: float = 10.0):
    import requests as rq
    try:
        url = 'https://www.googleapis.com/youtube/v3/i18nRegions?part=snippet&hl=en_US&maxResults=1'
        proxies = None
        p = (proxy or '').strip()
        if p:
            proxies = {'http': p, 'https': p}
        r = rq.get(url, timeout=float(timeout or 10), proxies=proxies)
        return {'ok': r.status_code == 200, 'status': r.status_code}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)

# ---- Profils: list/get/save/dup/delete/export/import ----

def _profiles_load_all():
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _profiles_save_all(data: dict):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return False
    return True

@app.get('/api/profiles')
async def api_profiles_list():
    d = _profiles_load_all()
    names = sorted(list(d.keys()))
    if 'default' not in names:
        names.insert(0, 'default')
    return {'ok': True, 'names': names}

@app.get('/api/profiles/{name}')
async def api_profiles_get(name: str):
    d = _profiles_load_all()
    return {'ok': True, 'name': name, 'data': d.get(name) or {}}

@app.post('/api/profiles/{name}')
async def api_profiles_save(name: str, request: Request):
    b = await request.json()
    d = _profiles_load_all()
    d[name] = b if isinstance(b, dict) else {}
    _profiles_save_all(d)
    return {'ok': True}

@app.post('/api/profiles/{name}/duplicate')
async def api_profiles_duplicate(name: str, request: Request):
    b = await request.json()
    new_name = (b.get('new_name') or '').strip()
    if not new_name:
        return JSONResponse({'error': 'new_name manquant'}, status_code=400)
    d = _profiles_load_all()
    if new_name in d:
        return JSONResponse({'error': 'existe déjà'}, status_code=409)
    base = d.get(name) or {}
    d[new_name] = dict(base)
    _profiles_save_all(d)
    return {'ok': True}

@app.delete('/api/profiles/{name}')
async def api_profiles_delete(name: str):
    if name == 'default':
        return JSONResponse({'error': "default ne peut être supprimé"}, status_code=400)
    d = _profiles_load_all()
    if name in d:
        try:
            del d[name]
        except Exception:
            pass
        _profiles_save_all(d)
    try:
        from t2y.auth import delete_token
        delete_token(name)
    except Exception:
        pass
    return {'ok': True}

@app.get('/api/profiles/export')
async def api_profiles_export():
    d = _profiles_load_all()
    data = json.dumps(d, ensure_ascii=False, indent=2).encode('utf-8')
    return Response(content=data, media_type='application/json', headers={'Content-Disposition': 'attachment; filename=profiles.json'})

@app.post('/api/profiles/import')
async def api_profiles_import(request: Request):
    b = await request.json()
    incoming = b.get('data')
    if not isinstance(incoming, dict):
        return JSONResponse({'error': 'format invalide'}, status_code=400)
    overwrite = bool(b.get('overwrite'))
    d = _profiles_load_all()
    for k, v in incoming.items():
        if (k in d) and not overwrite:
            continue
        if isinstance(v, dict):
            d[k] = v
    _profiles_save_all(d)
    return {'ok': True}

@app.get('/api/ping')
async def api_ping():
    return {'ok': True}

@app.get('/favicon.ico')
async def favicon():
    # Essayer de servir depuis static
    p = os.path.join('webapp', 'static', 'favicon.ico')
    if os.path.exists(p):
        return FileResponse(p)
    # fallback: 204
    return JSONResponse({}, status_code=204)

# --- Upload watermark file ---
@app.post('/api/upload/watermark')
async def api_upload_watermark(file: UploadFile = File(...)):
    try:
        # Valider extension basique
        name = file.filename or 'wm'
        ext = os.path.splitext(name)[1].lower()
        if ext not in ('.png', '.jpg', '.jpeg'):
            return JSONResponse({'error': 'Format non supporté (png/jpg)'}, status_code=400)
        # Dossier user config
        updir = CONFIG_DIR / 'uploads'
        updir.mkdir(parents=True, exist_ok=True)
        safe = ''.join(c for c in os.path.splitext(name)[0] if c.isalnum() or c in ('-','_','.')) or 'wm'
        dest = updir / f"{safe}{ext}"
        # Écrire fichier
        with open(dest, 'wb') as f:
            f.write(await file.read())
        # Retourner chemin absolu pour ffmpeg
        return {'ok': True, 'path': str(dest), 'url': f"/user-uploads/{dest.name}"}
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
