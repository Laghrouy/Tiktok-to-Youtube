import threading
import time
from typing import List, Dict, Optional

from t2y.metadata import fetch_tiktok_metadata
from t2y.downloader import download_tiktok_with_info
from t2y.uploader import upload_to_youtube, apply_post_upload_settings
from t2y.validators import parse_rfc3339
from t2y.config import CONFIG_DIR
from t2y.logger import log

import json
import os
import shutil
import subprocess

QUEUE_FILE = CONFIG_DIR / 'queue.json'
WATCH_FILE = CONFIG_DIR / 'watch.json'


class AppState:
    def __init__(self):
        self.queue: List[Dict] = []
        self.queue_running = False
        self.queue_paused = False
        self.watch_running = False
        self._watch_thread: Optional[threading.Thread] = None
        self._queue_thread: Optional[threading.Thread] = None
        self.interval_min = 10.0
        self.handle = ''
        self.quota = 3
        self.inc_kw = []
        self.exc_kw = []
        self.min_dur = 0
        self.max_dur = 0
        self.last_poll = ''
        self.last_video_id = ''
        self.pause_after_n_enabled = False
        self.pause_after_n_value = 0
        self._processed_in_run = 0
        self._seen = set()
        self._load_queue()
        self._load_watch()

    def _save_queue(self):
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.queue, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log('error', f'webapp: save queue failed: {e}')

    def _load_queue(self):
        try:
            with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
                self.queue = json.load(f)
        except Exception:
            self.queue = []

    def _save_watch(self):
        try:
            data = {
                'handle': self.handle,
                'seen': sorted(list(self._seen)),
                'interval': self.interval_min,
                'quota': self.quota,
                'inc_kw': self.inc_kw,
                'exc_kw': self.exc_kw,
                'min_dur': self.min_dur,
                'max_dur': self.max_dur,
                'last_poll': self.last_poll,
            }
            with open(WATCH_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log('error', f'webapp: save watch failed: {e}')

    def _load_watch(self):
        try:
            with open(WATCH_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            self.handle = d.get('handle') or ''
            self._seen = set(d.get('seen') or [])
            self.interval_min = float(d.get('interval') or 10)
            self.quota = int(d.get('quota') or 3)
            self.inc_kw = d.get('inc_kw') or []
            self.exc_kw = d.get('exc_kw') or []
            self.min_dur = int(d.get('min_dur') or 0)
            self.max_dur = int(d.get('max_dur') or 0)
            self.last_poll = d.get('last_poll') or ''
        except Exception:
            pass

    def queue_add(self, url: str, title: str = '', description: str = '', tags: Optional[list] = None, adv: Optional[dict] = None, privacy: str = 'private'):
        # Conserver compat avec anciens appels (tags simple)
        if adv is None:
            adv = {'tags': (tags or [])}
        # Sanitize tags (500 chars total)
        def _sanitize(tags_list):
            try:
                if not tags_list:
                    return []
                cleaned, seen, total = [], set(), 0
                for t in tags_list:
                    s = (t or '').strip().lstrip('#')
                    if not s:
                        continue
                    k = s.lower()
                    if k in seen:
                        continue
                    if total + len(s) > 500:
                        continue
                    cleaned.append(s)
                    seen.add(k)
                    total += len(s)
                return cleaned
            except Exception:
                return tags_list or []
        adv['tags'] = _sanitize(adv.get('tags') or [])
        item = {
            'iid': f'item_{len(self.queue)+1}',
            'url': url,
            'title': title,
            'description': description or '',
            'tags': adv.get('tags') or [],
            'privacy': (privacy or 'private'),
            'adv': adv,
            'status': 'en attente',
            'd_pct': 0,
            'u_pct': 0,
            'result': '',
            'results': {}
        }
        self.queue.append(item)
        self._save_queue()
        return item

    def _queue_worker(self):
        self.queue_running = True
        while self.queue_running:
            for it in list(self.queue):
                if not self.queue_running:
                    break
                while self.queue_paused and self.queue_running:
                    time.sleep(0.3)
                if it.get('status') == 'terminé':
                    continue
                it['status'] = 'en cours'
                self._save_queue()
                try:
                    vf = None
                    # download
                    adv = it.get('adv') or {}
                    # initialiser badges si absents
                    if 'badges' not in it or not isinstance(it.get('badges'), list):
                        it['badges'] = []
                    def _add_badge(b):
                        try:
                            if b not in it['badges']:
                                it['badges'].append(b)
                        except Exception:
                            pass
                    timeout = (adv.get('timeout') or '').strip() or None
                    proxy = (adv.get('proxy') or '').strip() or None
                    def _dl(p):
                        try:
                            it['d_pct'] = int(p)
                            it['status'] = 'téléchargement'
                            self._save_queue()
                        except Exception:
                            pass
                    vf, _info = download_tiktok_with_info(it['url'], timeout=timeout, proxy=proxy, on_progress=_dl)

                    # ffmpeg pré-traitement si demandé
                    try:
                        ff_mode = (adv.get('ff_mode') or 'none').strip()
                        ff_w = int(adv.get('ff_target_w') or 1080)
                        ff_h = int(adv.get('ff_target_h') or 1920)
                        ff_norm = bool(adv.get('ff_normalize'))
                        ff_remux = bool(adv.get('ff_remux'))
                        trim_start = str(adv.get('ff_trim_start') or '').strip()
                        trim_end = str(adv.get('ff_trim_end') or '').strip()
                        wm_path = (adv.get('ff_wm_path') or '').strip()
                        wm_pos = (adv.get('ff_wm_pos') or 'bottom-right').strip()
                        ff_selected = (ff_mode != 'none') or ff_norm or ff_remux or trim_start or trim_end or wm_path
                        # Ne pas tenter ffmpeg sur une vidéo qui semble invalide/vidée (stub) → échec assuré
                        min_valid_size = 64 * 1024  # 64KB
                        vf_ok = bool(vf and os.path.exists(vf) and os.path.getsize(vf) >= min_valid_size)
                        if ff_selected and not shutil.which('ffmpeg'):
                            log('error', 'ffmpeg introuvable — options ffmpeg ignorées')
                        if ff_selected and shutil.which('ffmpeg') and not vf_ok:
                            log('error', f"ffmpeg ignoré: entrée invalide/trop petite ({os.path.getsize(vf) if vf and os.path.exists(vf) else 0} bytes): {vf}")
                            _add_badge('ffskip')
                        if ff_selected and shutil.which('ffmpeg') and vf_ok:
                            it['status'] = 'pré-traitement vidéo'
                            it['f_pct'] = 0
                            self._save_queue()
                            out_path = vf + '.proc.mp4'
                            prev_vf = vf
                            vf_parts = []
                            af_parts = []
                            # mode vidéo
                            if ff_mode == 'crop_9_16':
                                vf_parts.append(f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale={ff_w}:{ff_h}")
                            elif ff_mode == 'pad_9_16':
                                vf_parts.append(f"scale={ff_w}:-2,pad={ff_w}:{ff_h}:(ow-iw)/2:(oh-ih)/2:black")
                            # audio normalize
                            if ff_norm:
                                af_parts.append('loudnorm=I=-16:LRA=11:TP=-1.5')
                            # position watermark
                            overlay_expr = {
                                'top-left': '10:10',
                                'top-right': f"W-w-10:10",
                                'bottom-left': '10:H-h-10',
                                'bottom-right': 'W-w-10:H-h-10'
                            }.get(wm_pos, 'W-w-10:H-h-10')
                            # Construire commande
                            cmd = ['ffmpeg', '-y']
                            # trim
                            if trim_start:
                                try:
                                    float(trim_start)
                                    cmd += ['-ss', str(trim_start)]
                                except Exception:
                                    pass
                            cmd += ['-i', vf]
                            if trim_end:
                                try:
                                    float(trim_end)
                                    cmd += ['-to', str(trim_end)]
                                except Exception:
                                    pass
                            map_args = []
                            filter_complex = None
                            if wm_path and os.path.exists(wm_path):
                                # overlay watermark
                                wm_chain = 'format=rgba'
                                if vf_parts:
                                    filter_complex = f"[0:v]{','.join(vf_parts)}[vbase];[1:v]{wm_chain}[wm];[vbase][wm]overlay={overlay_expr}[vout]"
                                else:
                                    filter_complex = f"[1:v]{wm_chain}[wm];[0:v][wm]overlay={overlay_expr}[vout]"
                                cmd += ['-i', wm_path, '-filter_complex', filter_complex, '-map', '[vout]']
                                map_args = ['-map', '0:a?']
                            elif vf_parts:
                                cmd += ['-vf', ','.join(vf_parts)]
                            # audio filter
                            if af_parts:
                                cmd += ['-af', ','.join(af_parts)]
                            # codecs
                            needs_encode = bool(vf_parts or af_parts or (wm_path and os.path.exists(wm_path)))
                            if needs_encode:
                                cmd += ['-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-c:a', 'aac', '-b:a', '192k']
                            else:
                                if ff_remux:
                                    cmd += ['-c', 'copy', '-movflags', '+faststart']
                            if map_args:
                                cmd += map_args
                            cmd += [out_path]
                            try:
                                # Flux live pour estimer la progression
                                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                                last = ''
                                # Estimation simple: bytes écrits vs. durée estimée inconnue → fallback à spinner progressif
                                step = 0
                                while True:
                                    line = proc.stdout.readline() if proc.stdout else ''
                                    if not line and proc.poll() is not None:
                                        break
                                    if line:
                                        last = line.strip()
                                        # Tentative de parse time= dans la sortie
                                        # Exemple: time=00:00:12.34
                                        import re
                                        m = re.search(r'time=(\d{2}):(\d{2}):(\d{2})[\.,](\d{2})', last)
                                        if m:
                                            hh, mm, ss, cs = map(int, m.groups())
                                            elapsed = hh*3600 + mm*60 + ss + cs/100.0
                                            # si l'info durée source est connue, approx
                                            src_dur = None
                                            try:
                                                src_dur = float((_info or {}).get('duration') or 0)
                                            except Exception:
                                                src_dur = None
                                            if src_dur and src_dur > 0:
                                                pct = int(max(0, min(100, (elapsed/src_dur)*100)))
                                                it['f_pct'] = pct
                                                self._save_queue()
                                    else:
                                        step = (step + 5) % 100
                                        if it.get('f_pct', 0) < 95:
                                            it['f_pct'] = max(it.get('f_pct', 0), step)
                                            self._save_queue()
                                rc = proc.wait()
                                if rc == 0 and os.path.exists(out_path):
                                    it['f_pct'] = 100
                                    self._save_queue()
                                    vf = out_path
                                    # nettoyer l'ancien fichier source si différent
                                    try:
                                        if prev_vf and prev_vf != vf and os.path.exists(prev_vf):
                                            os.remove(prev_vf)
                                    except Exception:
                                        pass
                                else:
                                    raise RuntimeError(f"ffmpeg exit {rc}; dernière ligne: {last}")
                            except Exception as e:
                                log('error', f"ffmpeg a échoué: {e}")
                    except Exception as _ffe:
                        log('error', f'pré-traitement ffmpeg: {_ffe}')

                    # Remux systématique en MP4 + faststart si aucun traitement explicite n'est demandé
                    try:
                        # Recalcule un indicateur local sans dépendre d'une variable potentiellement non définie
                        ff_mode_local = (adv.get('ff_mode') or 'none') if isinstance(adv, dict) else 'none'
                        ff_any = False
                        try:
                            m = str(ff_mode_local).strip().lower()
                            ff_any = (m != 'none') or bool(adv.get('ff_normalize') if isinstance(adv, dict) else False) or bool(
                                (adv.get('ff_pad_9_16') if isinstance(adv, dict) else False) or (adv.get('ff_pad_1_1') if isinstance(adv, dict) else False) or (adv.get('ff_pad_16_9') if isinstance(adv, dict) else False)
                            )
                        except Exception:
                            ff_any = False

                        if (not ff_any) and shutil.which('ffmpeg') and os.path.exists(vf):
                            it['status'] = 'préparation pour YouTube'
                            self._save_queue()
                            remux_out = vf + '.fast.mp4'
                            prev_vf = vf
                            cmd = ['ffmpeg', '-y', '-i', vf, '-c', 'copy', '-movflags', '+faststart', remux_out]
                            rc = subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            if rc == 0 and os.path.exists(remux_out) and os.path.getsize(remux_out) > 0:
                                vf = remux_out
                                _add_badge('prep')
                                # supprimer l'ancien fichier source
                                try:
                                    if prev_vf and prev_vf != vf and os.path.exists(prev_vf):
                                        os.remove(prev_vf)
                                except Exception:
                                    pass
                            else:
                                # fallback encode vers un MP4 standard (H.264/AAC/yuv420p)
                                enc_out = vf + '.enc.mp4'
                                cmd2 = ['ffmpeg', '-y', '-i', vf, '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', enc_out]
                                rc2 = subprocess.call(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                if rc2 == 0 and os.path.exists(enc_out) and os.path.getsize(enc_out) > 0:
                                    vf = enc_out
                                    _add_badge('prep')
                                    # supprimer l'ancien fichier source
                                    try:
                                        if prev_vf and prev_vf != vf and os.path.exists(prev_vf):
                                            os.remove(prev_vf)
                                    except Exception:
                                        pass
                                else:
                                    log('error', 'remux/encode MP4 a échoué — upload du fichier original')
                    except Exception as e:
                        log('error', f'remux MP4 échoué: {e}')

                    # upload
                    title = it.get('title') or ''
                    desc = it.get('description') or ''
                    privacy = it.get('privacy') or 'private'
                    def _ul(p):
                        try:
                            it['u_pct'] = int(p)
                            it['status'] = 'upload'
                            self._save_queue()
                        except Exception:
                            pass
                    # YouTube (optionnel via destinations)
                    dests = (adv.get('destinations') or {}) if isinstance(adv, dict) else {}
                    vid = None
                    if dests.get('yt', True):
                        vid = upload_to_youtube(vf, title, desc, privacy, on_progress=_ul, advanced=adv)
                        it['results'] = it.get('results') or {}
                        it['results']['yt'] = vid
                    try:
                        from t2y.auth import get_credentials as _get_creds
                        yt = _get_creds((adv.get('profile') or None))
                        apply_post_upload_settings(yt, vid, adv)
                    except Exception as e:
                        log('error', f'post-upload settings échoués: {e}')
                    # Instagram/TikTok (stubs)
                    try:
                        if dests.get('ig'):
                            from t2y.insta_uploader import upload_to_instagram
                            ig_id = upload_to_instagram(vf, caption=desc or title, on_progress=_ul, advanced=adv)
                            it['results']['ig'] = ig_id
                    except Exception as e:
                        log('error', f'instagram stub error: {e}')
                    try:
                        if dests.get('tt'):
                            from t2y.tiktok_poster import post_to_tiktok
                            tt_id = post_to_tiktok(vf, caption=desc or title, on_progress=_ul, advanced=adv)
                            it['results']['tt'] = tt_id
                    except Exception as e:
                        log('error', f'tiktok stub error: {e}')

                    it['status'] = 'terminé'
                    it['result'] = vid or it.get('results', {}).get('ig') or it.get('results', {}).get('tt') or ''
                    self.last_video_id = (it.get('results', {}).get('yt') or '')
                except Exception as e:
                    it['status'] = 'erreur'
                    it['result'] = str(e)
                finally:
                    try:
                        if vf and os.path.exists(vf):
                            os.remove(vf)
                            d = os.path.dirname(vf)
                            if os.path.isdir(d) and not os.listdir(d):
                                os.rmdir(d)
                    except Exception:
                        pass
                    self._save_queue()
                    # Pause automatique après N éléments si activée
                    try:
                        if self.pause_after_n_enabled:
                            n = int(self.pause_after_n_value or 0)
                            if n > 0:
                                self._processed_in_run += 1
                                if self._processed_in_run >= n:
                                    self.queue_paused = True
                                    self._processed_in_run = 0
                    except Exception:
                        pass
            # end for
            time.sleep(0.3)
        self.queue_running = False

    def start_queue(self):
        if not self.queue_running:
            self._processed_in_run = 0
            self._queue_thread = threading.Thread(target=self._queue_worker, daemon=True)
            self._queue_thread.start()

    def pause_queue(self, pause: bool):
        self.queue_paused = bool(pause)

    def stop_queue(self):
        self.queue_running = False

    def move_item(self, iid: str, direction: str) -> bool:
        try:
            idx = next((i for i, it in enumerate(self.queue) if it.get('iid') == iid), -1)
            if idx < 0:
                return False
            if direction == 'up' and idx > 0:
                self.queue[idx-1], self.queue[idx] = self.queue[idx], self.queue[idx-1]
            elif direction == 'down' and idx < len(self.queue)-1:
                self.queue[idx+1], self.queue[idx] = self.queue[idx], self.queue[idx+1]
            else:
                return False
            self._save_queue()
            return True
        except Exception:
            return False

    def clear_done(self) -> int:
        removed = 0
        try:
            newq = []
            for it in self.queue:
                if (it.get('status') or '') == 'terminé':
                    removed += 1
                    continue
                newq.append(it)
            self.queue = newq
            self._save_queue()
        except Exception:
            pass
        return removed

    def resume_errors(self) -> int:
        changed = 0
        try:
            for it in self.queue:
                if (it.get('status') or '') == 'erreur':
                    it['status'] = 'en attente'
                    it['d_pct'] = 0
                    it['u_pct'] = 0
                    changed += 1
            if changed:
                self._save_queue()
        except Exception:
            pass
        return changed

    def remove_item(self, iid: str) -> bool:
        idx = -1
        try:
            for i, it in enumerate(self.queue):
                if (it.get('iid') or '') == iid:
                    idx = i
                    break
            if idx >= 0:
                self.queue.pop(idx)
                self._save_queue()
                return True
        except Exception:
            pass
        return False

    def _watch_worker(self):
        self.watch_running = True
        while self.watch_running:
            try:
                handle = (self.handle or '').strip()
                if handle.startswith('@'):
                    handle = f'https://www.tiktok.com/{handle}'
                if not handle:
                    break
                # list videos flat
                try:
                    import yt_dlp
                except Exception:
                    yt_dlp = None
                urls = []
                if yt_dlp is not None:
                    with yt_dlp.YoutubeDL({'extract_flat': True, 'skip_download': True}) as ydl:
                        info = ydl.extract_info(handle, download=False)
                        for e in (info.get('entries') or []):
                            u = e.get('url') or e.get('webpage_url')
                            if u:
                                urls.append(u)
                added = 0
                for u in urls:
                    if not self.watch_running:
                        break
                    if u in self._seen:
                        continue
                    meta = fetch_tiktok_metadata(u) or {}
                    # Filtres (mots-clés + durée)
                    def _ok(meta):
                        try:
                            title = (meta.get('title') or '').lower()
                            desc = (meta.get('description') or '').lower()
                            text = f"{title} {desc}"
                            if self.inc_kw and not any((k or '').lower() in text for k in self.inc_kw):
                                return False
                            if self.exc_kw and any((k or '').lower() in text for k in self.exc_kw):
                                return False
                            dur = meta.get('duration') if isinstance(meta, dict) else None
                            try:
                                dur = int(dur) if dur is not None else None
                            except Exception:
                                dur = None
                            if self.min_dur and dur is not None and dur < int(self.min_dur):
                                return False
                            if self.max_dur and self.max_dur > 0 and dur is not None and dur > int(self.max_dur):
                                return False
                            return True
                        except Exception:
                            return True
                    if not _ok(meta):
                        continue
                    title = meta.get('title') or ''
                    desc = (meta.get('description') or '').strip()
                    tags = meta.get('hashtags') or []
                    self.queue_add(u, title, desc, tags)
                    self._seen.add(u)
                    self._save_watch()
                    added += 1
                    if self.quota and added >= self.quota:
                        break
            except Exception as e:
                log('error', f'webapp: watch error: {e}')
            # sleep interval
            t = max(1.0, float(self.interval_min or 10.0)) * 60.0
            try:
                from datetime import datetime
                self.last_poll = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                self._save_watch()
            except Exception:
                pass
            for _ in range(int(t)):
                if not self.watch_running:
                    break
                time.sleep(1)
        self.watch_running = False

    def start_watch(self, handle: str, interval_min: float, quota: int, inc_kw: list[str] | None = None, exc_kw: list[str] | None = None, min_dur: int = 0, max_dur: int = 0):
        self.handle = handle
        self.interval_min = float(interval_min or 10)
        self.quota = int(quota or 0)
        self.inc_kw = [str(x).strip() for x in (inc_kw or []) if str(x).strip()]
        self.exc_kw = [str(x).strip() for x in (exc_kw or []) if str(x).strip()]
        self.min_dur = int(min_dur or 0)
        self.max_dur = int(max_dur or 0)
        self._save_watch()
        if not self.watch_running:
            self._watch_thread = threading.Thread(target=self._watch_worker, daemon=True)
            self._watch_thread.start()

    def stop_watch(self):
        self.watch_running = False


state = AppState()
