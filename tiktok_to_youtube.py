import glob
import os
import pickle
import threading
import tempfile
import requests
import yt_dlp
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Floodgauge
from datetime import datetime
from pathlib import Path
import subprocess
import re
import json
import webbrowser
import shutil
import hashlib
import csv
import time
from t2y.constants import (
    SCOPES,
    DEFAULT_CATEGORY_ID,
    DEFAULT_TAGS,
    YOUTUBE_CATEGORIES,
    LANGUAGES,
    LICENSES,
    UPLOADS_DB,
)
from t2y.config import CONFIG_DIR, LOG_FILE, SETTINGS_FILE
from t2y.logger import log as core_log, set_level as set_log_level, get_level as get_log_level
from t2y.auth import get_credentials  # kept for compatibility in uploader
from t2y.auth import delete_token as auth_delete_token
# (import déjà fait plus haut)
from t2y.uploader import upload_to_youtube as core_upload_to_youtube, apply_post_upload_settings as core_apply_post_upload
from t2y.metadata import fetch_tiktok_metadata
from t2y.validators import is_valid_tiktok_url, parse_rfc3339
from google.auth.transport.requests import Request
from t2y.downloader import download_tiktok as core_download_tiktok, download_tiktok_with_info
from t2y.constants import PROFILES_FILE, WATCH_STATE_FILE

# État global simple pour annulation et progression
cancel_event = threading.Event()
_thumbnail_photo = None  # garder la ref pour Tk
_log_history = []  # buffer mémoire pour copier facilement (gardé pour compat, mais on lit via t2y.logger)

# Préparer répertoire config
try:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


def _ui_sink(line: str, level: str):
    try:
        # garder un historique en mémoire pour le bouton "Copier les logs"
        _log_history.append(line)
        log_text.configure(state='normal')
        tag = 'ERROR' if level.upper() == 'ERROR' else 'INFO'
        log_text.insert('end', line, tag)
        log_text.see('end')
        log_text.configure(state='disabled')
    except Exception:
        pass


def log(level: str, text: str):
    # délègue au logger central avec un sink UI
    core_log(level, text, ui_sink=lambda line, level: root.after(0, _ui_sink, line, level))


# --- Tooltips simples ---
class Tooltip:
    def __init__(self, widget, text: str):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self._show)
        widget.bind('<Leave>', self._hide)

    def _show(self, event=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self.tip, text=self.text, justify='left', background='#111', foreground='#eee',
                       relief='solid', borderwidth=1, padx=6, pady=4)
        lbl.pack()

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def attach_tooltip(widget, text: str):
    try:
        Tooltip(widget, text)
    except Exception:
        pass

def download_tiktok(url, on_progress=None):
    def _progress(pct: float):
        if cancel_event.is_set():
            raise Exception("Opération annulée par l’utilisateur")
        if on_progress:
            on_progress(pct)
    return core_download_tiktok(url, _progress)
def _ydl_progress_hook(d, on_progress):
    # obsolète: conservé pour compat éventuelle, non utilisé par download_tiktok
    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
    downloaded = d.get("downloaded_bytes", 0)
    if total and on_progress:
        pct = max(0.0, min(100.0, (downloaded / total) * 100.0))
        on_progress(pct)

def get_credentials(profile=None, force_reauth: bool = False):
    """Wrapper local pour obtenir le client YouTube authentifié.
    Accepte un profil et un indicateur de réauthentification pour rester compatible
    avec t2y.auth.get_credentials(profile, force_reauth).
    """
    from t2y.auth import get_credentials as _gc
    return _gc(profile, force_reauth=force_reauth)

def upload_to_youtube(video_path, title, description, privacy, on_progress=None, advanced=None):
    def _progress(pct: float):
        if cancel_event.is_set():
            raise Exception("Opération annulée par l’utilisateur")
        if on_progress:
            on_progress(pct)
    return core_upload_to_youtube(video_path, title, description, privacy, _progress, advanced)


def apply_post_upload_settings(video_id, advanced):
    prof = None
    try:
        if isinstance(advanced, dict):
            prof = (advanced.get('profile') or '').strip() or None
    except Exception:
        prof = None
    yt = get_credentials(prof)
    return core_apply_post_upload(yt, video_id, advanced)

def _file_sha256(path: str, block=1024*1024):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _load_uploads_db():
    try:
        with open(UPLOADS_DB, 'r', encoding='utf-8') as f:
            import json as _json
            return _json.load(f)
    except Exception:
        return {}


def _save_uploads_db(db):
    try:
        from pathlib import Path
        Path(UPLOADS_DB).parent.mkdir(parents=True, exist_ok=True)
        with open(UPLOADS_DB, 'w', encoding='utf-8') as f:
            import json as _json
            _json.dump(db, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def process():
    url = entry_url.get().strip()
    title = entry_title.get().strip()
    description = text_desc.get("1.0", tk.END).strip()
    privacy = privacy_var.get()

    # Récupérer options avancées
    # Tags depuis l'UI uniquement pour process() manuel
    tags_input = tags_var.get().strip()
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else None
    tags = _sanitize_tags_500(tags) if tags else tags
    cat_name = category_var.get()
    category_id = YOUTUBE_CATEGORIES.get(cat_name) or DEFAULT_CATEGORY_ID  # Utiliser la catégorie par défaut
    lang_name = language_var.get()
    default_lang = LANGUAGES.get(lang_name)
    made_for_kids = made_for_kids_var.get()
    license_name = license_var.get()
    license_val = LICENSES.get(license_name)
    draft = draft_var.get()
    publish_at_raw = schedule_var.get().strip()
    rec_date_raw = recording_date_var.get().strip()
    publish_at = parse_rfc3339(publish_at_raw) if publish_at_raw else None
    rec_date = parse_rfc3339(rec_date_raw) if rec_date_raw else None
    loc_desc = location_desc_var.get().strip() or None
    lat_val = latitude_var.get().strip() or None
    lon_val = longitude_var.get().strip() or None
    playlists_input = playlists_var.get().strip()
    playlists = [p.strip() for p in playlists_input.split(",") if p.strip()] if playlists_input else []

    advanced = {
        "tags": tags,
        "categoryId": category_id,
        "defaultLanguage": default_lang,
        "madeForKids": made_for_kids,
        "license": license_val,
        "draft": draft,
        "publishAt": publish_at,
        "recordingDate": rec_date,
        "locationDescription": loc_desc,
        "latitude": lat_val,
        "longitude": lon_val,
        "playlists": playlists,
        "timeout": (timeout_var.get().strip() if 'timeout_var' in globals() else ''),
        "proxy": (proxy_var.get().strip() if 'proxy_var' in globals() else ''),
        "profile": (profile_var.get().strip() if 'profile_var' in globals() else ''),
        "uploadChunkMB": (upload_chunk_mb_var.get().strip() if 'upload_chunk_mb_var' in globals() else ''),
        "uploadMaxRetries": (upload_retries_var.get().strip() if 'upload_retries_var' in globals() else ''),
    }

    if not url or not title:
        messagebox.showerror("Erreur", "URL TikTok et Titre YouTube sont requis.")
        log('error', 'Champs requis manquants (URL ou Titre)')
        return

    # reset état
    cancel_event.clear()
    set_status("Téléchargement en cours…")
    btn_start.configure(state=DISABLED)
    btn_cancel.configure(state=NORMAL)
    set_download_progress(0.0)
    set_upload_progress(0.0)

    def _notify(title: str, body: str, success: bool):
        try:
            if shutil.which('notify-send'):
                icon = 'dialog-information' if success else 'dialog-error'
                subprocess.Popen(['notify-send', '--icon', icon, title, body])
        except Exception:
            pass
        try:
            root.bell()
        except Exception:
            pass


    def work():
        video_file = None
        try:
            log('info', 'Traitement démarré')
            # Télécharger avec métadonnées pour détection Shorts
            video_file, info = download_tiktok_with_info(
                url,
                on_progress=set_download_progress,
                proxy=(advanced.get('proxy') or '').strip() or None,
                timeout=(advanced.get('timeout') or '').strip() or None,
            )
            duration = info.get('duration') if isinstance(info, dict) else None  # Durée de la vidéo
            width = info.get('width') if isinstance(info, dict) else None  # Largeur de la vidéo
            height = info.get('height') if isinstance(info, dict) else None  # Hauteur de la vidéo

            description_local = description
            is_vertical = (isinstance(width, (int, float)) and isinstance(height, (int, float)) and height > width)
            is_short = (isinstance(duration, (int, float)) and duration < 60)
            recropped_by_short = False

            if is_vertical and is_short:
                cur_tags = advanced.get('tags') or []
                if not any((t.strip().lower() == 'shorts') for t in cur_tags if isinstance(t, str)):
                    cur_tags = list(cur_tags) + ['Shorts']
                    advanced['tags'] = cur_tags
                if '#Shorts' not in description_local:
                    description_local = (description_local + ' #Shorts').strip()
                log('info', 'Détection Shorts: vidéo <60s et verticale → ajout #Shorts et tag Shorts')
                try:
                    dtxt = int(duration) if isinstance(duration, (int, float)) else '?'
                    wtxt = int(width) if isinstance(width, (int, float)) else '?'
                    htxt = int(height) if isinstance(height, (int, float)) else '?'
                    set_shorts_info(f"Short détecté: {dtxt} s, {wtxt}x{htxt} (vertical)", SUCCESS)
                except Exception:
                    set_shorts_info("Short détecté", SUCCESS)
            elif is_short and not is_vertical:
                # Recadrage optionnel 9:16 si activé
                try:
                    if autocrop_var.get():
                        if shutil.which('ffmpeg'):
                            in_path = video_file
                            out_path = os.path.join(os.path.dirname(in_path), f"shorts_{os.path.basename(in_path)}")
                            filter_str = "crop=ih*9/16:ih:(iw - ih*9/16)/2:0,scale=1080:1920"
                            cmd = [
                                'ffmpeg', '-y', '-i', in_path,
                                '-vf', filter_str,
                                '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23',
                                '-c:a', 'aac', '-b:a', '128k',
                                out_path
                            ]
                            log('info', 'Recadrage 9:16 en cours (ffmpeg)…')
                            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            video_file = out_path
                            recropped_by_short = True
                            # Ajout marquage Shorts après recadrage
                            cur_tags = advanced.get('tags') or []
                            if not any((t.strip().lower() == 'shorts') for t in cur_tags if isinstance(t, str)):
                                cur_tags = list(cur_tags) + ['Shorts']
                                advanced['tags'] = cur_tags
                            if '#Shorts' not in description_local:
                                description_local = (description_local + ' #Shorts').strip()
                            log('info', 'Recadrage terminé → marqué #Shorts')
                            try:
                                dtxt = int(duration) if isinstance(duration, (int, float)) else '?'
                                set_shorts_info(f"Recadré 9:16 → Short: {dtxt} s, 1080x1920", SUCCESS)
                            except Exception:
                                set_shorts_info("Recadré 9:16 → Short", SUCCESS)
                        else:
                            log('error', "ffmpeg introuvable — impossible de recadrer automatiquement en 9:16")
                            try:
                                dtxt = int(duration) if isinstance(duration, (int, float)) else '?'
                                wtxt = int(width) if isinstance(width, (int, float)) else '?'
                                htxt = int(height) if isinstance(height, (int, float)) else '?'
                                set_shorts_info(f"Courte ({dtxt} s) non verticale {wtxt}x{htxt} — ffmpeg manquant", WARNING)
                            except Exception:
                                set_shorts_info("Courte non verticale — ffmpeg manquant", WARNING)
                    else:
                        log('info', 'Vidéo <60s mais non verticale — non marquée #Shorts (activez le recadrage 9:16 pour le forcer).')
                        try:
                            dtxt = int(duration) if isinstance(duration, (int, float)) else '?'
                            wtxt = int(width) if isinstance(width, (int, float)) else '?'
                            htxt = int(height) if isinstance(height, (int, float)) else '?'
                            set_shorts_info(f"Courte ({dtxt} s) non verticale {wtxt}x{htxt} — activez le recadrage 9:16", WARNING)
                        except Exception:
                            set_shorts_info("Courte non verticale — activez le recadrage 9:16", WARNING)
                except Exception as e:
                    log('error', f"Recadrage 9:16 échoué: {e}")
                    set_shorts_info("Recadrage 9:16 échoué", DANGER)
            else:
                # Pas un short
                set_shorts_info("")

            # Détection doublons par hash (avant traitements ffmpeg facultatifs pour éviter de dupliquer)
            try:
                h = _file_sha256(video_file)
                db = _load_uploads_db()
                if h in db:
                    prev = db.get(h)
                    log('error', f"Doublon détecté: déjà uploadé (ID={prev.get('id')}, titre='{prev.get('title')}')")
                    raise Exception("Vidéo déjà uploadée (doublon détecté)")
            except Exception as e:
                if 'doublon' in str(e).lower():
                    raise
                log('error', f"Impossible de vérifier le doublon: {e}")

            # Traitement ffmpeg optionnel (remux, padding/recadrage, normalisation audio, trim, watermark)
            def _parse_float(s):
                try:
                    return float(s)
                except Exception:
                    return None

            try:
                ff_selected = (
                    ff_remux_var.get() or ff_normalize_var.get() or ff_mode_var.get() != 'none' or
                    (ff_trim_start_var.get().strip() != '' or ff_trim_end_var.get().strip() != '') or
                    (ff_wm_path_var.get().strip() != '')
                )
            except Exception:
                ff_selected = False

            if ff_selected and shutil.which('ffmpeg'):
                in_path = video_file
                out_path = os.path.join(os.path.dirname(in_path), f"proc_{os.path.basename(in_path)}")
                start_s = _parse_float(ff_trim_start_var.get().strip()) if ff_trim_start_var.get().strip() else None
                end_s = _parse_float(ff_trim_end_var.get().strip()) if ff_trim_end_var.get().strip() else None

                mode = ff_mode_var.get()
                try:
                    target_w = int(ff_target_w_var.get())
                    target_h = int(ff_target_h_var.get())
                except Exception:
                    target_w, target_h = 1080, 1920

                wm_path = ff_wm_path_var.get().strip()
                wm_pos = ff_wm_pos_var.get()
                wm_opacity = ff_wm_opacity_var.get()

                # Construire filtres vidéo
                vf_parts = []
                if mode == 'crop_9_16' and not recropped_by_short:
                    vf_parts.append(f"crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale={target_w}:{target_h}")
                elif mode == 'pad_9_16' and not recropped_by_short:
                    # Mise à l'échelle puis padding centré
                    vf_parts.append(f"scale={target_w}:-2,pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:black")

                # Gestion watermark via second entrée ou overlay simple
                use_wm = bool(wm_path)
                overlay_expr = {
                    'top-left': '10:10',
                    'top-right': f'{target_w}-w-10:10',
                    'bottom-left': '10:main_h-h-10',
                    'bottom-right': f'main_w-w-10:main_h-h-10',
                }.get(wm_pos or 'bottom-right', 'main_w-w-10:main_h-h-10')

                # Audio
                af_parts = []
                if ff_normalize_var.get():
                    af_parts.append('loudnorm=I=-16:LRA=11:TP=-1.5')

                # Re-encodage requis ?
                reencode_video = (mode in ('crop_9_16', 'pad_9_16') and not recropped_by_short) or use_wm or (start_s is not None or end_s is not None)
                reencode_audio = ff_normalize_var.get() or (start_s is not None or end_s is not None)

                cmd = ['ffmpeg', '-y']
                # Trim rapide: -ss avant -i, et -t si possible
                if start_s is not None:
                    cmd += ['-ss', str(max(0.0, start_s))]
                cmd += ['-i', in_path]
                if use_wm:
                    cmd += ['-i', wm_path]

                # Filtres vidéo
                filter_complex = None
                if use_wm:
                    # préparer éventuelle opacité du watermark
                    wm_chain = 'format=rgba'
                    alpha = max(0.0, min(1.0, float(wm_opacity))) if isinstance(wm_opacity, (int, float)) else 1.0
                    if alpha < 1.0:
                        wm_chain += f",colorchannelmixer=aa={alpha}"
                    if vf_parts:
                        filter_complex = f"[0:v]{','.join(vf_parts)}[v0];[1:v]{wm_chain}[wm];[v0][wm]overlay={overlay_expr}"
                    else:
                        filter_complex = f"[1:v]{wm_chain}[wm];[0:v][wm]overlay={overlay_expr}"
                else:
                    if vf_parts:
                        cmd += ['-vf', ','.join(vf_parts)]

                # Audio filter
                if af_parts:
                    cmd += ['-af', ','.join(af_parts)]

                if filter_complex:
                    cmd += ['-filter_complex', filter_complex]

                # Durée (-t) si end fourni
                if end_s is not None:
                    if start_s is not None and end_s > start_s:
                        cmd += ['-t', str(end_s - start_s)]
                    elif start_s is None and end_s > 0:
                        cmd += ['-t', str(end_s)]

                # Codecs
                if reencode_video:
                    cmd += ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23']
                else:
                    # Remux si demandé, sinon copie vidéo si rien à faire
                    if ff_remux_var.get():
                        cmd += ['-c:v', 'copy']
                    else:
                        cmd += ['-c:v', 'copy']
                if reencode_audio:
                    cmd += ['-c:a', 'aac', '-b:a', '128k']
                else:
                    cmd += ['-c:a', 'copy']

                cmd += ['-movflags', '+faststart', out_path]

                log('info', 'Traitement ffmpeg…')
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    # Remplacer le fichier d'entrée par la sortie
                    try:
                        if in_path and os.path.exists(in_path):
                            os.remove(in_path)
                    except Exception:
                        pass
                    video_file = out_path
                    log('info', 'ffmpeg: OK')
                except Exception as e:
                    log('error', f"ffmpeg a échoué: {e}")
            elif ff_selected and not shutil.which('ffmpeg'):
                log('error', "ffmpeg introuvable — options ffmpeg ignorées")

            set_status("Upload en cours…")
            video_id = upload_to_youtube(
                video_file, title, description_local, privacy, on_progress=set_upload_progress, advanced=advanced
            )
            # Post-traitement: enregistrement et playlists
            apply_post_upload_settings(video_id, advanced)
            # Journaliser l'upload pour doublons (après succès)
            try:
                h = _file_sha256(video_file)
                db = _load_uploads_db()
                db[h] = {"id": video_id, "title": title}
                _save_uploads_db(db)
            except Exception as e:
                log('error', f"Impossible d'enregistrer l'upload: {e}")
            set_status(f"✅ Upload terminé ! ID : {video_id}")
            log('info', f'Succès: vidéo en ligne ID={video_id}')
            last_video_id.set(video_id or "")
            root.after(0, lambda: [btn_open_video.configure(state=NORMAL), btn_copy_id.configure(state=NORMAL)])
            _notify("Upload terminé", f"ID: {video_id}", True)
            root.after(0, lambda: messagebox.showinfo("Succès", f"Vidéo mise en ligne !\nID : {video_id}"))
        except Exception as e:
            root.after(0, lambda: messagebox.showerror("Erreur", str(e)))
            set_status("❌ Échec.")
            log('error', f'Échec: {e}')
            _notify("Échec de l’upload", str(e), False)
        finally:
            try:
                if video_file and os.path.exists(video_file):
                    os.remove(video_file)
                    # supprimer le dossier temp si vide
                    temp_dir = os.path.dirname(video_file)
                    if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
            except Exception:
                pass
            root.after(0, lambda: [btn_start.configure(state=NORMAL), btn_cancel.configure(state=DISABLED)])

    threading.Thread(target=work, daemon=True).start()


def cancel_action():
    cancel_event.set()
    set_status("Annulation en cours…")
    log('info', 'Annulation demandée par l’utilisateur')


def prefill_from_tiktok():
    url = entry_url.get().strip()
    if not url:
        messagebox.showwarning("Info", "Entrez d’abord une URL TikTok.")
        log('error', 'Préremplir: URL manquante')
        return
    try:
        set_status("Récupération des métadonnées…")
        log('info', 'Récupération des métadonnées TikTok …')
        info = fetch_tiktok_metadata(url)
        if info:
            if info.get('title'):
                root.after(0, lambda: entry_title.delete(0, tk.END))
                root.after(0, lambda: entry_title.insert(0, info['title']))
            if info.get('description'):
                root.after(0, lambda: text_desc.delete("1.0", tk.END))
                root.after(0, lambda: text_desc.insert("1.0", info['description']))
            if info.get('thumbnail'):
                _set_thumbnail_image(info['thumbnail'])
            # Hashtags -> Tags YouTube
            try:
                hashtags = info.get('hashtags') or []
                if isinstance(hashtags, list) and hashtags:
                    # Récupérer tags existants et fusionner
                    existing = [t.strip() for t in (tags_var.get() or '').split(',') if t.strip()]
                    merged = []
                    seen = set()
                    for t in existing + hashtags:
                        tt = t.strip().lstrip('#')
                        if tt and tt.lower() not in seen:
                            seen.add(tt.lower())
                            merged.append(tt)
                    # Optionnel: limiter à 20 tags pour rester raisonnable
                    if len(merged) > 20:
                        merged = merged[:20]
                    tags_var.set(', '.join(merged))
                    log('info', f"Tags préremplis depuis TikTok: {', '.join(merged)}")
            except Exception as _e:
                log('error', f"Impossible d'extraire les hashtags: {_e}")
        log('info', 'Métadonnées récupérées')
        set_status("Métadonnées chargées.")
    except Exception as e:
        set_status("Impossible de charger les métadonnées.")
        messagebox.showerror("Erreur", str(e))
def _set_thumbnail_image(url):
    global _thumbnail_photo
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        img = Image.open(tempfile.SpooledTemporaryFile())
    except Exception:
        # fallback direct depuis bytes
        try:
            from io import BytesIO
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
        except Exception:
            return
    # Redimensionner
    max_w = 360
    max_h = 220
    w, h = img.size
    ratio = min(max_w / float(w), max_h / float(h), 1.0)
    if ratio < 1.0:
        img = img.resize((int(w * ratio), int(h * ratio)))
    _thumbnail_photo = ImageTk.PhotoImage(img)
    thumb_label.configure(image=_thumbnail_photo)
    thumb_label.image = _thumbnail_photo

# Helpers de mise à jour UI thread-safe
def set_status(text):
    root.after(0, lambda: status_label.configure(text=text))


def set_download_progress(pct):
    def _upd():
        download_var.set(pct)
        try:
            download_pb.configure(text=f"{pct:.0f}%")
        except Exception:
            pass
    root.after(0, _upd)


def set_upload_progress(pct):
    def _upd():
        upload_var.set(pct)
        try:
            upload_pb.configure(text=f"{pct:.0f}%")
        except Exception:
            pass
    root.after(0, _upd)


# Helper pour afficher une pastille d'information Shorts
def set_shorts_info(text: str = "", style=INFO):
    def _upd():
        try:
            shorts_info_label.configure(text=text, bootstyle=style)
        except Exception:
            pass
    root.after(0, _upd)

# Helper: limiter les tags à 500 caractères combinés (YouTube)
def _sanitize_tags_500(tags_list):
    try:
        if not tags_list:
            return tags_list
        cleaned = []
        seen = set()
        total = 0
        truncated = False
        for t in tags_list:
            if not isinstance(t, str):
                continue
            s = t.strip()
            if not s:
                continue
            key = s.lower()
            if key in seen:
                continue
            # si ce tag dépasse le budget, essayer de voir si un plus petit passera ensuite
            if total + len(s) > 500:
                truncated = True
                continue
            cleaned.append(s)
            seen.add(key)
            total += len(s)
        if truncated:
            log('info', f"Tags tronqués pour respecter la limite de 500 caractères (retenus: {len(cleaned)})")
        return cleaned
    except Exception:
        return tags_list

# ---- Interface Tkinter avec ttkbootstrap ----
root = tb.Window(themename="darkly")
root.title("TikTok → YouTube Uploader")
root.geometry("980x700")
try:
    root.minsize(900, 600)
except Exception:
    pass

# Menu Fenêtre (reset & centrage)
def _center_window(w, h):
    try:
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        x = max(0, int((sw - w) / 2))
        y = max(0, int((sh - h) / 3))
        return f"{w}x{h}+{x}+{y}"
    except Exception:
        return f"{w}x{h}+50+50"

def on_reset_and_center():
    try:
        # Taille par défaut cohérente avec le démarrage
        geom = _center_window(980, 700)
        root.geometry(geom)
        root.after(50, lambda: (root.deiconify(), root.lift()))
        set_status('Fenêtre recentrée')
        save_settings()
    except Exception:
        pass

menubar = tk.Menu(root)
menu_window = tk.Menu(menubar, tearoff=0)
menu_window.add_command(label='Réinitialiser et centrer', command=on_reset_and_center)
menubar.add_cascade(label='Fenêtre', menu=menu_window)
try:
    root.config(menu=menubar)
except Exception:
    pass

# Charger paramètres (thème et géométrie)
def load_settings():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_settings():
    data = {
        'theme': theme_var.get() if 'theme_var' in globals() else 'darkly',
        'geometry': root.winfo_geometry(),
        # préférences additionnelles
        'logLevel': get_log_level(),
        'privacy': privacy_var.get() if 'privacy_var' in globals() else 'public',
        'previewVisible': preview_toggle_var.get() if 'preview_toggle_var' in globals() else True,
        'profile': profile_var.get().strip() if 'profile_var' in globals() else 'default',
        'pauseAfterNEnabled': pause_after_n_var.get() if 'pause_after_n_var' in globals() else False,
        'pauseAfterNValue': pause_after_n_value.get().strip() if 'pause_after_n_value' in globals() else '0',
        'uploadChunkMB': upload_chunk_mb_var.get().strip() if 'upload_chunk_mb_var' in globals() else '8',
        'uploadMaxRetries': upload_retries_var.get().strip() if 'upload_retries_var' in globals() else '8',
        'watchAutostart': watch_autostart_var.get() if 'watch_autostart_var' in globals() else False,
        'ffmpegPath': ffmpeg_path_var.get().strip() if 'ffmpeg_path_var' in globals() else '',
    }
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass

settings = load_settings()
if settings.get('geometry'):
    def _safe_set_geometry(geom: str):
        try:
            import re
            sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
            m = re.match(r"^(\d+)x(\d+)\+(\-?\d+)\+(\-?\d+)$", str(geom))
            if not m:
                root.geometry("980x700")
                return
            w, h, x, y = map(int, m.groups())
            # bornes minimales
            w = max(900, min(w, sw))
            h = max(600, min(h, sh))
            # veiller à ce que la fenêtre reste visible (bordures 40px)
            x = max(- (w - 40), min(x, sw - 40))
            y = max(0, min(y, sh - 40))
            root.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            try:
                root.geometry("980x700")
            except Exception:
                pass
    _safe_set_geometry(settings['geometry'])
else:
    # Centrer et s'assurer que la fenêtre est visible et devant
    try:
        geom = _center_window(980, 700)
        root.geometry(geom)
        root.after(100, lambda: (root.deiconify(), root.lift()))
    except Exception:
        pass


# Scroll global (Canvas + Scrollbar)
viewport = tb.Frame(root)
viewport.pack(fill=BOTH, expand=YES)

canvas = tk.Canvas(viewport, highlightthickness=0)
vsb = tb.Scrollbar(viewport, orient='vertical', command=canvas.yview)
canvas.configure(yscrollcommand=vsb.set)
canvas.pack(side=LEFT, fill=BOTH, expand=YES)
vsb.pack(side=RIGHT, fill=Y)

container = tb.Frame(canvas, padding=15)
_cw = canvas.create_window((0, 0), window=container, anchor='nw')

def _on_container_configure(event=None):
    canvas.configure(scrollregion=canvas.bbox('all'))
    # Ajuster largeur frame interne à canvas
    try:
        canvas.itemconfig(_cw, width=canvas.winfo_width())
    except Exception:
        pass

container.bind('<Configure>', _on_container_configure)

def _on_mousewheel(event):
    # Windows / Mac / Linux
    delta = 0
    if event.num == 4:
        delta = -1
    elif event.num == 5:
        delta = 1
    elif event.delta:
        delta = -1 * int(event.delta / 120)
    if delta:
        canvas.yview_scroll(delta, 'units')

canvas.bind_all('<MouseWheel>', _on_mousewheel)
canvas.bind_all('<Button-4>', _on_mousewheel)
canvas.bind_all('<Button-5>', _on_mousewheel)

# En-tête avec titre et sélecteur de thème
header = tb.Frame(container)
header.pack(fill=X, pady=(0, 12))
title_lbl = tb.Label(header, text="TikTok → YouTube Uploader", font=("Segoe UI", 20, "bold"))
title_lbl.pack(side=LEFT)

theme_var = tk.StringVar(value=settings.get('theme', "darkly"))
try:
    root.style.theme_use(theme_var.get())
except Exception:
    pass
themes = ["darkly", "superhero", "cyborg", "solar", "flatly", "minty", "cosmo", "journal", "morph"]
tb.Label(header, text="Thème:").pack(side=LEFT, padx=(20, 6))
theme_combo = tb.Combobox(header, values=themes, textvariable=theme_var, width=12, state="readonly")
theme_combo.pack(side=LEFT)

def _on_theme_change(event=None):
    try:
        root.style.theme_use(theme_var.get())
        save_settings()
    except Exception:
        pass

theme_combo.bind("<<ComboboxSelected>>", _on_theme_change)

form = tb.Frame(container)
form.pack(fill=X, pady=5)

tb.Label(form, text="URL TikTok :").grid(row=0, column=0, sticky=W, padx=(0, 10))
entry_url = tb.Entry(form, width=70)
url_var = tk.StringVar()
entry_url.configure(textvariable=url_var)
entry_url.grid(row=0, column=1, pady=5, sticky=EW)
url_valid_label = tb.Label(form, text="", bootstyle=SECONDARY)
url_valid_label.grid(row=0, column=3, padx=(8,0), sticky=W)
prefill_btn = tb.Button(form, text="Préremplir", bootstyle=INFO, command=prefill_from_tiktok)
prefill_btn.grid(row=0, column=2, padx=6)

tb.Label(form, text="Titre YouTube :").grid(row=1, column=0, sticky=W, padx=(0, 10))
title_var = tk.StringVar()
entry_title = tb.Entry(form, width=70, textvariable=title_var)
entry_title.grid(row=1, column=1, pady=5, sticky=EW)

tb.Label(form, text="Description :").grid(row=2, column=0, sticky=NW, padx=(0, 10))
text_desc = ScrolledText(form, width=70, height=8, wrap=tk.WORD)
text_desc.grid(row=2, column=1, pady=5, sticky=EW)

tb.Label(form, text="Visibilité :").grid(row=3, column=0, sticky=W, padx=(0, 10))
privacy_var = tk.StringVar(value=settings.get('privacy', "public"))
privacy_combo = tb.Combobox(form, textvariable=privacy_var, values=["public", "unlisted", "private"], width=20, state="readonly")
privacy_combo.grid(row=3, column=1, pady=5, sticky=W)
privacy_combo.bind('<<ComboboxSelected>>', lambda e: save_settings())

def _profiles_names():
    data = _profiles_load_all()
    names = sorted(list(data.keys()))
    if 'default' not in names:
        names.insert(0, 'default')
    return names

# Helpers profils (charger/sauvegarder) avant usage
def _profiles_load_all():
    try:
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _profiles_save_all(data):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log('error', f"Sauvegarde profils échouée: {e}")

# Profil OAuth (Combobox)
tb.Label(form, text="Profil YouTube :").grid(row=3, column=2, sticky=E, padx=(10, 6))
profile_var = tk.StringVar(value=settings.get('profile', 'default'))
profile_combo = tb.Combobox(form, textvariable=profile_var, values=_profiles_names(), width=18, state='readonly')
profile_combo.grid(row=3, column=3, sticky=W)
def _refresh_profiles_combo():
    try:
        profile_combo.configure(values=_profiles_names())
    except Exception:
        pass
btns_prof = tb.Frame(form)
btns_prof.grid(row=3, column=4, sticky=W, padx=(6,0))
def _apply_profile_to_ui(pname: str):
    data = _profiles_load_all()
    p = data.get(pname or '')
    if not p:
        return
    try:
        if p.get('privacy'):
            privacy_var.set(p['privacy'])
        if p.get('tags'):
            tags_var.set(', '.join(p['tags']))
        if p.get('playlists'):
            playlists_var.set(', '.join(p['playlists']))
        if p.get('language'):
            if p['language'] in LANGUAGES:
                language_var.set(p['language'])
        if p.get('license'):
            if p['license'] in LICENSES:
                license_var.set(p['license'])
        if 'madeForKids' in p:
            made_for_kids_var.set(bool(p['madeForKids']))
        # ffmpeg presets
        if p.get('ff_mode'):
            ff_mode_var.set(p['ff_mode'])
        if p.get('ff_target_w'):
            ff_target_w_var.set(str(p['ff_target_w']))
        if p.get('ff_target_h'):
            ff_target_h_var.set(str(p['ff_target_h']))
        if 'ff_normalize' in p:
            ff_normalize_var.set(bool(p['ff_normalize']))
        if 'ff_remux' in p:
            ff_remux_var.set(bool(p['ff_remux']))
        if 'autocrop_short' in p:
            autocrop_var.set(bool(p['autocrop_short']))
    except Exception:
        pass
def _collect_ui_to_profile():
    try:
        tags_list = [t.strip() for t in (tags_var.get() or '').split(',') if t.strip()]
        playlists_list = [p.strip() for p in (playlists_var.get() or '').split(',') if p.strip()]
        return {
            'privacy': privacy_var.get(),
            'tags': tags_list,
            'playlists': playlists_list,
            'language': language_var.get(),
            'license': license_var.get(),
            'madeForKids': bool(made_for_kids_var.get()),
            # ffmpeg
            'ff_mode': ff_mode_var.get(),
            'ff_target_w': int(ff_target_w_var.get() or '1080'),
            'ff_target_h': int(ff_target_h_var.get() or '1920'),
            'ff_normalize': bool(ff_normalize_var.get()),
            'ff_remux': bool(ff_remux_var.get()),
            'autocrop_short': bool(autocrop_var.get()),
        }
    except Exception:
        return {}
def on_profile_load():
    _apply_profile_to_ui(profile_var.get().strip())
def on_profile_save():
    pname = profile_var.get().strip() or 'default'
    data = _profiles_load_all()
    data[pname] = _collect_ui_to_profile()
    _profiles_save_all(data)
    _refresh_profiles_combo()
    set_status(f"Preset profil '{pname}' enregistré")
tb.Button(btns_prof, text='Charger', bootstyle=SECONDARY, command=on_profile_load).pack(side=LEFT)
tb.Button(btns_prof, text='Enregistrer', bootstyle=INFO, command=on_profile_save).pack(side=LEFT, padx=(6,0))

# Déconnexion / Ré-auth immédiate
def on_profile_disconnect():
    pname = profile_var.get().strip() or 'default'
    try:
        auth_delete_token(pname)
        set_status(f"Token OAuth supprimé pour '{pname}'")
        log('info', f"Profil '{pname}': token supprimé")
    except Exception as e:
        messagebox.showerror('Erreur', f"Échec suppression token: {e}")
        return
    try:
        if messagebox.askyesno('Re-auth', 'Voulez-vous vous reconnecter maintenant ?'):
            def _reauth():
                try:
                    get_credentials(pname, force_reauth=True)
                    root.after(0, lambda: messagebox.showinfo('Re-auth', 'Connexion réussie.'))
                    log('info', 'Re-auth réussie')
                except Exception as e:
                    root.after(0, lambda: messagebox.showerror('Re-auth', f"Échec: {e}"))
                    log('error', f"Re-auth échouée: {e}")
            threading.Thread(target=_reauth, daemon=True).start()
    except Exception:
        pass

tb.Button(btns_prof, text='Déconnecter/Re-auth', bootstyle=DANGER, command=on_profile_disconnect).pack(side=LEFT, padx=(6,0))

# Dupliquer profil
def on_profile_duplicate():
    src = profile_var.get().strip() or 'default'
    data = _profiles_load_all()
    base = data.get(src) or _collect_ui_to_profile()
    if not isinstance(base, dict):
        base = {}
    new_name = simpledialog.askstring('Dupliquer profil', 'Nouveau nom du profil:', initialvalue=f"{src}_copy")
    if not new_name:
        return
    new_name = new_name.strip()
    if not new_name:
        return
    if new_name in data:
        messagebox.showerror('Erreur', f"Le profil '{new_name}' existe déjà.")
        return
    data[new_name] = dict(base)
    _profiles_save_all(data)
    _refresh_profiles_combo()
    try:
        profile_var.set(new_name)
        _apply_profile_to_ui(new_name)
    except Exception:
        pass
    set_status(f"Profil dupliqué → '{new_name}'")

# Supprimer profil
def on_profile_delete():
    pname = profile_var.get().strip() or 'default'
    if pname == 'default':
        messagebox.showwarning('Info', "Le profil 'default' ne peut pas être supprimé.")
        return
    if not messagebox.askyesno('Confirmer', f"Supprimer le profil '{pname}' ?\nLe token OAuth associé sera également supprimé."):
        return
    data = _profiles_load_all()
    if pname in data:
        try:
            del data[pname]
        except Exception:
            pass
    _profiles_save_all(data)
    try:
        auth_delete_token(pname)
    except Exception:
        pass
    # Choisir un profil restant
    remaining = sorted(list(data.keys()))
    next_name = 'default'
    if remaining:
        next_name = remaining[0] if 'default' not in remaining else 'default'
    _refresh_profiles_combo()
    try:
        profile_var.set(next_name)
        _apply_profile_to_ui(next_name)
    except Exception:
        pass
    set_status(f"Profil '{pname}' supprimé")

tb.Button(btns_prof, text='Dupliquer', bootstyle=SECONDARY, command=on_profile_duplicate).pack(side=LEFT, padx=(12,0))
tb.Button(btns_prof, text='Supprimer', bootstyle=DANGER, command=on_profile_delete).pack(side=LEFT, padx=(6,0))

# Exporter profils (JSON)
def on_profiles_export():
    try:
        data = _profiles_load_all()
        if not data:
            if not messagebox.askyesno('Exporter', "Aucun profil enregistré. Exporter quand même un fichier vide ?"):
                return
        path = filedialog.asksaveasfilename(
            title='Exporter profils',
            defaultextension='.json',
            filetypes=[('JSON', '*.json')],
            initialfile='profiles.json'
        )
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        set_status(f'Profils exportés → {path}')
        log('info', f'Export profils: {path}')
    except Exception as e:
        messagebox.showerror('Erreur', f"Export échoué: {e}")

# Importer profils (JSON) avec gestion collisions
def on_profiles_import():
    try:
        path = filedialog.askopenfilename(title='Importer profils', filetypes=[('JSON', '*.json')])
        if not path:
            return
        with open(path, 'r', encoding='utf-8') as f:
            incoming = json.load(f)
        if not isinstance(incoming, dict):
            messagebox.showerror('Erreur', "Fichier de profils invalide (format non conforme).")
            return
        data = _profiles_load_all()
        names_in = list(incoming.keys())
        collisions = [n for n in names_in if n in data]
        if collisions:
            resp = messagebox.askyesnocancel(
                'Collisions',
                "Certains profils existent déjà:\n- " + "\n- ".join(collisions) + "\n\nOui = écraser, Non = ignorer existants, Annuler = abandon"
            )
            if resp is None:
                return
            overwrite = bool(resp)
        else:
            overwrite = True
        imported = 0
        for name, value in incoming.items():
            if not isinstance(name, str) or not isinstance(value, dict):
                continue
            if (name in data) and not overwrite:
                continue
            data[name] = value
            imported += 1
        _profiles_save_all(data)
        _refresh_profiles_combo()
        set_status(f"Profils importés: {imported}")
        log('info', f"Import profils depuis {path}: {imported} entrées")
    except Exception as e:
        messagebox.showerror('Erreur', f"Import échoué: {e}")

tb.Button(btns_prof, text='Exporter', bootstyle=SECONDARY, command=on_profiles_export).pack(side=LEFT, padx=(12,0))
tb.Button(btns_prof, text='Importer', bootstyle=INFO, command=on_profiles_import).pack(side=LEFT, padx=(6,0))

# Auto démarrer la queue
auto_start_queue_var = tk.BooleanVar(value=False)
tb.Checkbutton(btns_prof, text='Auto démarrer la file', variable=auto_start_queue_var, bootstyle=SECONDARY).pack(side=LEFT, padx=(12,0))

def _on_profile_changed(*_):
    save_settings()
    # Charger automatiquement les presets du profil actif
    _apply_profile_to_ui(profile_var.get().strip())
profile_var.trace_add('write', _on_profile_changed)

# Charger presets du profil par défaut au démarrage
def _post_start_auto_actions():
    try:
        _apply_profile_to_ui(profile_var.get().strip())
        if auto_start_queue_var.get():
            on_queue_start()
    except Exception:
        pass
root.after(200, _post_start_auto_actions)

# Options avancées
adv = tb.Labelframe(container, text="Options avancées", bootstyle=SECONDARY)
adv.pack(fill=X, pady=10)

# Tags (séparés par des virgules)
tb.Label(adv, text="Tags (virgules) :").grid(row=0, column=0, sticky=W, padx=(0, 10))
tags_var = tk.StringVar(value="")
tags_entry = tb.Entry(adv, textvariable=tags_var)
tags_entry.grid(row=0, column=1, sticky=EW, pady=4)

# Catégorie
tb.Label(adv, text="Catégorie :").grid(row=1, column=0, sticky=W, padx=(0, 10))
category_var = tk.StringVar(value="People & Blogs")
tb.Combobox(adv, textvariable=category_var, values=list(YOUTUBE_CATEGORIES.keys()), state="readonly", width=28).grid(row=1, column=1, sticky=W, pady=4)

# Langue
tb.Label(adv, text="Langue :").grid(row=2, column=0, sticky=W, padx=(0, 10))
language_var = tk.StringVar(value="Français (fr)")
tb.Combobox(adv, textvariable=language_var, values=list(LANGUAGES.keys()), state="readonly", width=28).grid(row=2, column=1, sticky=W, pady=4)

# Made for Kids
made_for_kids_var = tk.BooleanVar(value=False)
tb.Checkbutton(adv, text="Contenu pour enfants (madeForKids)", variable=made_for_kids_var, bootstyle=INFO).grid(row=3, column=1, sticky=W, pady=4)
tb.Label(adv, text="").grid(row=3, column=0)  # aligner

# Licence
tb.Label(adv, text="Licence :").grid(row=4, column=0, sticky=W, padx=(0, 10))
license_var = tk.StringVar(value="Standard YouTube")
tb.Combobox(adv, textvariable=license_var, values=list(LICENSES.keys()), state="readonly", width=28).grid(row=4, column=1, sticky=W, pady=4)

# Localisation
tb.Label(adv, text="Localisation :").grid(row=5, column=0, sticky=NW, padx=(0, 10))
loc_frame = tb.Frame(adv)
loc_frame.grid(row=5, column=1, sticky=EW, pady=4)
location_desc_var = tk.StringVar()
latitude_var = tk.StringVar()
longitude_var = tk.StringVar()
tb.Entry(loc_frame, textvariable=location_desc_var, width=40).grid(row=0, column=0, columnspan=4, sticky=EW, pady=(0, 4))
tb.Label(loc_frame, text="Lat:").grid(row=1, column=0, sticky=E, padx=(0, 6))
tb.Entry(loc_frame, textvariable=latitude_var, width=12).grid(row=1, column=1, sticky=W)
tb.Label(loc_frame, text="Lon:").grid(row=1, column=2, sticky=E, padx=(6, 6))
tb.Entry(loc_frame, textvariable=longitude_var, width=12).grid(row=1, column=3, sticky=W)

# Date d'enregistrement
tb.Label(adv, text="Date d’enregistrement (RFC3339) :").grid(row=6, column=0, sticky=W, padx=(0, 10))
recording_date_var = tk.StringVar()
recording_date_entry = tb.Entry(adv, textvariable=recording_date_var, width=30)
recording_date_entry.grid(row=6, column=1, sticky=W, pady=4)
rec_date_status = tb.Label(adv, text="", bootstyle=SECONDARY)
rec_date_status.grid(row=6, column=2, sticky=W, padx=(8, 0))

# Playlists (IDs séparés par des virgules)
tb.Label(adv, text="Playlists (IDs, virgules) :").grid(row=7, column=0, sticky=W, padx=(0, 10))
playlists_var = tk.StringVar()
playlists_entry = tb.Entry(adv, textvariable=playlists_var)
playlists_entry.grid(row=7, column=1, sticky=EW, pady=4)

# Brouillon et Planification
draft_var = tk.BooleanVar(value=False)
tb.Checkbutton(adv, text="Brouillon (ne pas publier maintenant)", variable=draft_var, bootstyle=WARNING).grid(row=8, column=1, sticky=W, pady=4)
tb.Label(adv, text="Publier le (RFC3339 UTC):").grid(row=9, column=0, sticky=W, padx=(0, 10))
schedule_var = tk.StringVar()
schedule_entry = tb.Entry(adv, textvariable=schedule_var, width=30)
schedule_entry.grid(row=9, column=1, sticky=W, pady=4)
schedule_status = tb.Label(adv, text="", bootstyle=SECONDARY)
schedule_status.grid(row=9, column=2, sticky=W, padx=(8, 0))

# Option recadrage Shorts 9:16 si vidéo courte non verticale
autocrop_var = tk.BooleanVar(value=False)
tb.Checkbutton(adv, text="Recadrer en 9:16 si <60s", variable=autocrop_var, bootstyle=INFO).grid(row=10, column=1, sticky=W, pady=4)

# ----- Options ffmpeg (facultatives)
ff_frame = tb.Labelframe(adv, text="Options ffmpeg (facultatif)", bootstyle=SECONDARY)
ff_frame.grid(row=11, column=0, columnspan=3, sticky=EW, pady=(8, 0))

# Mode vidéo: aucun, recadrage 9:16, padding 9:16
tb.Label(ff_frame, text="Mode vidéo:").grid(row=0, column=0, sticky=W)
ff_mode_var = tk.StringVar(value='none')
ff_mode_combo = tb.Combobox(ff_frame, textvariable=ff_mode_var, state='readonly', values=['none', 'crop_9_16', 'pad_9_16'], width=12)
ff_mode_combo.grid(row=0, column=1, sticky=W, padx=(6, 12))

# Dimensions cibles
tb.Label(ff_frame, text="Cible (LxH):").grid(row=0, column=2, sticky=E)
ff_target_w_var = tk.StringVar(value='1080')
ff_target_h_var = tk.StringVar(value='1920')
tb.Entry(ff_frame, textvariable=ff_target_w_var, width=6).grid(row=0, column=3, sticky=W)
tb.Entry(ff_frame, textvariable=ff_target_h_var, width=6).grid(row=0, column=4, sticky=W, padx=(6, 0))

# Normalisation audio
ff_normalize_var = tk.BooleanVar(value=False)
tb.Checkbutton(ff_frame, text="Normaliser audio (EBU R128)", variable=ff_normalize_var, bootstyle=INFO).grid(row=1, column=0, columnspan=2, sticky=W, pady=4)

# Remux (copie codecs)
ff_remux_var = tk.BooleanVar(value=False)
tb.Checkbutton(ff_frame, text="Remux (faststart)", variable=ff_remux_var, bootstyle=SECONDARY).grid(row=1, column=2, columnspan=2, sticky=W, pady=4)

# Trim simple
tb.Label(ff_frame, text="Trim début (s):").grid(row=2, column=0, sticky=E)
ff_trim_start_var = tk.StringVar()
tb.Entry(ff_frame, textvariable=ff_trim_start_var, width=8).grid(row=2, column=1, sticky=W)
tb.Label(ff_frame, text="Trim fin (s):").grid(row=2, column=2, sticky=E)
ff_trim_end_var = tk.StringVar()
tb.Entry(ff_frame, textvariable=ff_trim_end_var, width=8).grid(row=2, column=3, sticky=W)

# Watermark léger
tb.Label(ff_frame, text="Watermark (PNG):").grid(row=3, column=0, sticky=E)
ff_wm_path_var = tk.StringVar()

def _pick_wm():
    p = filedialog.askopenfilename(title='Choisir une image watermark', filetypes=[('Images', '*.png;*.jpg;*.jpeg')])
    if p:
        ff_wm_path_var.set(p)

wm_entry = tb.Entry(ff_frame, textvariable=ff_wm_path_var)
wm_entry.grid(row=3, column=1, columnspan=3, sticky=EW)
tb.Button(ff_frame, text='…', bootstyle=INFO, command=_pick_wm, width=3).grid(row=3, column=4, sticky=W, padx=(6, 0))

tb.Label(ff_frame, text="Position:").grid(row=4, column=0, sticky=E)
ff_wm_pos_var = tk.StringVar(value='bottom-right')
tb.Combobox(ff_frame, textvariable=ff_wm_pos_var, state='readonly', values=['top-left','top-right','bottom-left','bottom-right'], width=14).grid(row=4, column=1, sticky=W)

tb.Label(ff_frame, text="Opacité:").grid(row=4, column=2, sticky=E)
ff_wm_opacity_var = tk.DoubleVar(value=0.3)
tb.Entry(ff_frame, textvariable=ff_wm_opacity_var, width=6).grid(row=4, column=3, sticky=W)

for c in range(5):
    ff_frame.columnconfigure(c, weight=(1 if c in (1,3) else 0))

# Détection ffmpeg
ffmpeg_path_var = tk.StringVar(value='')
ffmpeg_status_lbl = tb.Label(ff_frame, text="ffmpeg: inconnu", bootstyle=SECONDARY)
ffmpeg_status_lbl.grid(row=5, column=0, columnspan=5, sticky=W, pady=(6,0))

def _detect_ffmpeg():
    try:
        # priorité au chemin personnalisé si fourni
        custom = (ffmpeg_path_var.get() or '').strip()
        exe = custom if custom else shutil.which('ffmpeg')
        if not exe:
            ffmpeg_status_lbl.configure(text='ffmpeg introuvable — certaines fonctions seront inactives', bootstyle=DANGER)
            return
        # version
        try:
            r = subprocess.run([exe, '-version'], capture_output=True, text=True, timeout=3)
            out = (r.stdout or r.stderr or '').splitlines()[0] if (r.stdout or r.stderr) else ''
        except Exception:
            out = ''
        ffmpeg_status_lbl.configure(text=f'ffmpeg: {exe} {("- " + out) if out else ""}', bootstyle=SUCCESS)
    except Exception:
        ffmpeg_status_lbl.configure(text='ffmpeg: erreur de détection', bootstyle=DANGER)

def _pick_ffmpeg():
    p = filedialog.askopenfilename(title='Sélectionner ffmpeg', filetypes=[('ffmpeg', 'ffmpeg*;*.exe;*')])
    if p:
        ffmpeg_path_var.set(p)
        _detect_ffmpeg()
        save_settings()

btn_ffmpeg_pick = tb.Button(ff_frame, text='Choisir ffmpeg…', bootstyle=INFO, command=_pick_ffmpeg)
btn_ffmpeg_pick.grid(row=6, column=0, sticky=W, pady=(4,0))

# Charger chemin personnalisé et détecter
try:
    ff_custom = settings.get('ffmpegPath')
    if ff_custom:
        ffmpeg_path_var.set(str(ff_custom))
    _detect_ffmpeg()
except Exception:
    pass

# Réseau / Timeouts
net_frame = tb.Frame(adv)
net_frame.grid(row=12, column=0, columnspan=3, sticky=EW, pady=(8, 0))
tb.Label(net_frame, text="Timeout upload (s):").grid(row=0, column=0, sticky=E)
timeout_var = tk.StringVar(value='60')
tb.Entry(net_frame, textvariable=timeout_var, width=8).grid(row=0, column=1, sticky=W)
tb.Label(net_frame, text="Proxy (ex: http://user:pass@host:port)").grid(row=0, column=2, sticky=E, padx=(12, 6))
proxy_var = tk.StringVar()
tb.Entry(net_frame, textvariable=proxy_var).grid(row=0, column=3, sticky=EW)
net_frame.columnconfigure(3, weight=1)

# Upload tuning
tb.Label(net_frame, text="Chunk (MB):").grid(row=1, column=0, sticky=E, pady=(6,0))
upload_chunk_mb_var = tk.StringVar(value='8')
tb.Entry(net_frame, textvariable=upload_chunk_mb_var, width=8).grid(row=1, column=1, sticky=W, pady=(6,0))
tb.Label(net_frame, text="Retries:").grid(row=1, column=2, sticky=E, padx=(12,6), pady=(6,0))
upload_retries_var = tk.StringVar(value='8')
tb.Entry(net_frame, textvariable=upload_retries_var, width=8).grid(row=1, column=3, sticky=W, pady=(6,0))

# Test de connexion & indicateur proxy
def _mask_proxy_url(u: str) -> str:
    try:
        from urllib.parse import urlparse
        p = urlparse(u)
        host = p.hostname or ''
        port = f":{p.port}" if p.port else ''
        scheme = p.scheme or 'http'
        return f"{scheme}://{host}{port}"
    except Exception:
        return u

net_test_status_label = tb.Label(net_frame, text="", bootstyle=SECONDARY)
net_test_status_label.grid(row=2, column=2, columnspan=2, sticky=W, pady=(6,0))

net_proxy_info_label = tb.Label(net_frame, text="Proxy: (aucun)", bootstyle=SECONDARY)
net_proxy_info_label.grid(row=3, column=0, columnspan=4, sticky=W, pady=(4,0))

def _update_proxy_info_label(*_):
    try:
        ui_proxy = (proxy_var.get() or '').strip()
        http_p = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy') or ''
        https_p = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy') or ''
        parts = []
        if ui_proxy:
            parts.append(f"UI={_mask_proxy_url(ui_proxy)}")
        if http_p:
            parts.append(f"HTTP={_mask_proxy_url(http_p)}")
        if https_p:
            parts.append(f"HTTPS={_mask_proxy_url(https_p)}")
        if parts:
            net_proxy_info_label.configure(text="Proxy: " + ", ".join(parts), bootstyle=INFO)
        else:
            net_proxy_info_label.configure(text="Proxy: (aucun)", bootstyle=SECONDARY)
    except Exception:
        try:
            net_proxy_info_label.configure(text="Proxy: (indisponible)", bootstyle=SECONDARY)
        except Exception:
            pass

def on_test_youtube():
    net_test_status_label.configure(text="Test en cours…", bootstyle=WARNING)
    def _run():
        try:
            url = 'https://www.googleapis.com/youtube/v3/i18nRegions?part=snippet&hl=en_US&maxResults=1'
            proxies = None
            p = (proxy_var.get() or '').strip()
            if p:
                proxies = {'http': p, 'https': p}
            r = requests.get(url, timeout=10, proxies=proxies)
            if r.status_code == 200:
                root.after(0, lambda: net_test_status_label.configure(text="Connexion OK", bootstyle=SUCCESS))
                set_status('Test de connexion: OK')
            else:
                root.after(0, lambda: net_test_status_label.configure(text=f"Échec HTTP {r.status_code}", bootstyle=DANGER))
                set_status(f'Test de connexion échoué: HTTP {r.status_code}')
        except Exception as e:
            root.after(0, lambda: net_test_status_label.configure(text=f"Erreur: {e}", bootstyle=DANGER))
            set_status(f'Test de connexion: erreur {e}')
    threading.Thread(target=_run, daemon=True).start()

tb.Button(net_frame, text='Tester connexion YouTube', bootstyle=INFO, command=on_test_youtube).grid(row=2, column=0, columnspan=2, sticky=W, pady=(6,0))

# Charger état des options d’upload (après création)
try:
    if settings.get('uploadChunkMB') is not None:
        upload_chunk_mb_var.set(str(settings.get('uploadChunkMB')))
    if settings.get('uploadMaxRetries') is not None:
        upload_retries_var.set(str(settings.get('uploadMaxRetries')))
except Exception:
    pass

# Sauvegarde automatique à la saisie
def _bind_upload_opts_save(*_):
    try:
        save_settings()
    except Exception:
        pass
try:
    upload_chunk_mb_var.trace_add('write', _bind_upload_opts_save)
    upload_retries_var.trace_add('write', _bind_upload_opts_save)
except Exception:
    pass

# Mettre à jour l'indicateur proxy au démarrage et sur changements
try:
    _update_proxy_info_label()
    proxy_var.trace_add('write', lambda *_: _update_proxy_info_label())
except Exception:
    pass

adv.columnconfigure(1, weight=1)
# Zone miniature + contrôles
preview_toggle_var = tk.BooleanVar(value=settings.get('previewVisible', True))
toggle_frame = tb.Frame(container)
toggle_frame.pack(fill=X)
tb.Checkbutton(toggle_frame, text="Afficher l’aperçu", variable=preview_toggle_var, bootstyle=INFO, command=lambda: _toggle_preview()).pack(anchor=W)

preview_frame = tb.Labelframe(container, text="Aperçu", bootstyle=INFO)
preview_frame.pack(fill=X, pady=10)
thumb_label = tb.Label(preview_frame, text="Miniature indisponible", anchor=CENTER)
thumb_label.pack(fill=X, pady=8)

def _toggle_preview():
    if preview_toggle_var.get():
        preview_frame.pack(fill=X, pady=10)
    else:
        preview_frame.forget()
    save_settings()

# Appliquer l'état initial de l'aperçu
root.after(0, _toggle_preview)

# Progression
progress_frame = tb.Labelframe(container, text="Progression", bootstyle=SUCCESS)
progress_frame.pack(fill=X, pady=10)

download_var = tk.DoubleVar(value=0)
upload_var = tk.DoubleVar(value=0)

tb.Label(progress_frame, text="Téléchargement").pack(anchor=W)
download_pb = Floodgauge(progress_frame, variable=download_var, maximum=100, bootstyle=INFO, text="0%")
download_pb.pack(fill=X, padx=4, pady=(2, 8))

tb.Label(progress_frame, text="Upload").pack(anchor=W)
upload_pb = Floodgauge(progress_frame, variable=upload_var, maximum=100, bootstyle=SUCCESS, text="0%")
upload_pb.pack(fill=X, padx=4, pady=(2, 8))

# Pastille d'info Shorts
shorts_info_label = tb.Label(container, text="", bootstyle=INFO)
shorts_info_label.pack(fill=X, pady=(0, 6))

# File d’attente
queue_frame = tb.Labelframe(container, text="File d’attente", bootstyle=PRIMARY)
queue_frame.pack(fill=BOTH, expand=YES, pady=10)

queue_toolbar = tb.Frame(queue_frame)
queue_toolbar.pack(fill=X)

def queue_add_item(url: str, title: str = "", description: str | None = None, tags: list[str] | None = None):
    iid = f"item_{len(queue_items)+1}"
    queue_items.append({
        'iid': iid,
        'url': url,
        'title': title,
        'description': description or '',
        'tags': tags or [],
        'status': 'en attente',
        'd_pct': 0,
        'u_pct': 0,
        'result': ''
    })
    queue_tree.insert('', 'end', iid=iid, values=(url, title, 'en attente', '0%', '0%', ''))
    _queue_save()

def on_queue_add():
    u = url_var.get().strip()
    t = title_var.get().strip()
    if not u:
        messagebox.showwarning('Info', "Entrez d’abord une URL.")
        return
    queue_add_item(u, t)

def on_queue_import():
    paths = filedialog.askopenfilenames(title='Importer TXT/CSV', filetypes=[('TXT/CSV', '*.txt;*.csv')])
    if not paths:
        return
    for p in paths:
        try:
            if p.lower().endswith('.csv'):
                with open(p, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if not row:
                            continue
                        url = row[0].strip()
                        title = (row[1].strip() if len(row) > 1 else '')
                        if url:
                            queue_add_item(url, title)
            else:
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        # format possible: url[,titre]
                        if ',' in line:
                            url, title = line.split(',', 1)
                        else:
                            url, title = line, ''
                        if url.strip():
                            queue_add_item(url.strip(), title.strip())
        except Exception as e:
            log('error', f"Import échoué {p}: {e}")
    _queue_save()

def on_queue_remove():
    for sel in queue_tree.selection():
        queue_tree.delete(sel)
        for i, it in list(enumerate(queue_items)):
            if it['iid'] == sel:
                queue_items.pop(i)
                break
    _queue_save()

def on_queue_up():
    sel = queue_tree.selection()
    if not sel:
        return
    iid = sel[0]
    index = queue_tree.index(iid)
    if index > 0:
        queue_tree.move(iid, '', index - 1)
    queue_items.insert(index - 1, queue_items.pop(index))
    _queue_save()

def on_queue_down():
    sel = queue_tree.selection()
    if not sel:
        return
    iid = sel[0]
    index = queue_tree.index(iid)
    queue_tree.move(iid, '', index + 1)
    queue_items.insert(index + 1, queue_items.pop(index))
    _queue_save()

tb.Button(queue_toolbar, text='Ajouter', bootstyle=SUCCESS, command=on_queue_add).pack(side=LEFT)
tb.Button(queue_toolbar, text='Importer…', bootstyle=INFO, command=on_queue_import).pack(side=LEFT, padx=(6,0))
tb.Button(queue_toolbar, text='Supprimer', bootstyle=DANGER, command=on_queue_remove).pack(side=LEFT, padx=(6,0))
tb.Button(queue_toolbar, text='Monter', bootstyle=SECONDARY, command=on_queue_up).pack(side=LEFT, padx=(12,0))
tb.Button(queue_toolbar, text='Descendre', bootstyle=SECONDARY, command=on_queue_down).pack(side=LEFT, padx=(6,0))

queue_cols = ('url', 'title', 'status', 'd_pct', 'u_pct', 'result')
queue_tree = tb.Treeview(queue_frame, columns=queue_cols, show='headings', height=6)
for c, lbl in zip(queue_cols, ['URL', 'Titre', 'Statut', 'D%', 'U%', 'Résultat']):
    queue_tree.heading(c, text=lbl)
    queue_tree.column(c, width=120 if c in ('status','d_pct','u_pct') else 260, anchor='w')
queue_tree.pack(fill=BOTH, expand=YES, padx=4, pady=6)

import json as _json
QUEUE_FILE = CONFIG_DIR / 'queue.json'
queue_items = []

def _queue_save():
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
            _json.dump(queue_items, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log('error', f"Sauvegarde queue échouée: {e}")

def _queue_load():
    try:
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            items = _json.load(f)
            queue_items.clear()
            resumable = 0
            total = 0
            for it in items:
                iid = it.get('iid') or f"item_{len(queue_items)+1}"
                it['iid'] = iid
                # Normaliser statuts transitoires vers 'en attente'
                status = (it.get('status') or 'en attente')
                if status in ('en cours', 'téléchargement', 'upload'):
                    status = 'en attente'
                it['status'] = status
                total += 1
                if status != 'terminé':
                    resumable += 1
                queue_items.append(it)
                queue_tree.insert('', 'end', iid=iid, values=(it.get('url',''), it.get('title',''), status, f"{it.get('d_pct',0)}%", f"{it.get('u_pct',0)}%", it.get('result','')))
            try:
                _queue_save()  # persister les statuts normalisés
            except Exception:
                pass
            try:
                set_status(f"File chargée: {resumable}/{total} à reprendre (terminés ignorés)")
            except Exception:
                pass
    except Exception:
        pass

# Charger la queue persistée
root.after(0, _queue_load)

# --- Surveillance TikTok (poll) ---
watch_frame = tb.Labelframe(container, text="Surveillance TikTok (poll)", bootstyle=INFO)
watch_frame.pack(fill=X, pady=10)

tb.Label(watch_frame, text="Profil/Handle TikTok (URL ou @handle):").grid(row=0, column=0, sticky=W)
watch_handle_var = tk.StringVar()
tb.Entry(watch_frame, textvariable=watch_handle_var).grid(row=0, column=1, sticky=EW)

tb.Label(watch_frame, text="Intervalle (min):").grid(row=0, column=2, sticky=E, padx=(10, 6))
watch_interval_var = tk.StringVar(value='10')
tb.Entry(watch_frame, textvariable=watch_interval_var, width=6).grid(row=0, column=3, sticky=W)

tb.Label(watch_frame, text="Durée min (s):").grid(row=1, column=0, sticky=E, padx=(0,6))
watch_min_dur_var = tk.StringVar(value='0')
tb.Entry(watch_frame, textvariable=watch_min_dur_var, width=8).grid(row=1, column=1, sticky=W)

tb.Label(watch_frame, text="Durée max (s):").grid(row=1, column=2, sticky=E, padx=(10,6))
watch_max_dur_var = tk.StringVar(value='0')
tb.Entry(watch_frame, textvariable=watch_max_dur_var, width=8).grid(row=1, column=3, sticky=W)

tb.Label(watch_frame, text="Inclure mots-clés (CSV):").grid(row=2, column=0, sticky=E)
watch_inc_kw_var = tk.StringVar()
tb.Entry(watch_frame, textvariable=watch_inc_kw_var).grid(row=2, column=1, sticky=EW)

tb.Label(watch_frame, text="Exclure mots-clés (CSV):").grid(row=2, column=2, sticky=E, padx=(10,6))
watch_exc_kw_var = tk.StringVar()
tb.Entry(watch_frame, textvariable=watch_exc_kw_var).grid(row=2, column=3, sticky=EW)

tb.Label(watch_frame, text="Quota max par poll:").grid(row=3, column=0, sticky=E)
watch_quota_var = tk.StringVar(value='3')
tb.Entry(watch_frame, textvariable=watch_quota_var, width=6).grid(row=3, column=1, sticky=W)

watch_running = False
_watch_seen = set()

def _watch_load_state():
    try:
        with open(WATCH_STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        handle = data.get('handle') or ''
        seen = set(data.get('seen') or [])
        watch_handle_var.set(handle)
        # config
        if data.get('interval'):
            watch_interval_var.set(str(data['interval']))
        if data.get('min_dur') is not None:
            watch_min_dur_var.set(str(data['min_dur']))
        if data.get('max_dur') is not None:
            watch_max_dur_var.set(str(data['max_dur']))
        if data.get('inc_kw') is not None:
            watch_inc_kw_var.set(', '.join(data['inc_kw']))
        if data.get('exc_kw') is not None:
            watch_exc_kw_var.set(', '.join(data['exc_kw']))
        if data.get('quota') is not None:
            watch_quota_var.set(str(data['quota']))
        try:
            last = data.get('last_poll') or ''
            if last:
                watch_last_poll_var.set(last)
        except Exception:
            pass
        return seen
    except Exception:
        return set()

def _watch_save_state():
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            'handle': watch_handle_var.get().strip(),
            'seen': sorted(list(_watch_seen)),
            'interval': watch_interval_var.get(),
            'min_dur': watch_min_dur_var.get(),
            'max_dur': watch_max_dur_var.get(),
            'inc_kw': _split_csv(watch_inc_kw_var.get()),
            'exc_kw': _split_csv(watch_exc_kw_var.get()),
            'quota': watch_quota_var.get(),
            'last_poll': watch_last_poll_var.get(),
        }
        with open(WATCH_STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log('error', f"Watch: sauvegarde état échouée: {e}")

def _split_csv(s):
    return [t.strip().lower() for t in (s or '').split(',') if t.strip()]

def _filters_ok(meta, inc_kw, exc_kw, min_d, max_d):
    try:
        title = (meta.get('title') or '').lower()
        desc = (meta.get('description') or '').lower()
        text = f"{title} {desc}"
        if inc_kw and not any(k in text for k in inc_kw):
            return False
        if exc_kw and any(k in text for k in exc_kw):
            return False
        # durée en secondes si disponible
        dur = meta.get('duration') if isinstance(meta, dict) else None
        try:
            dur = int(dur) if dur is not None else None
        except Exception:
            dur = None
        if min_d and dur is not None and dur < min_d:
            return False
        if max_d and max_d > 0 and dur is not None and dur > max_d:
            return False
        return True
    except Exception:
        return True

def _watch_worker():
    import time as _time
    from t2y.metadata import fetch_tiktok_metadata
    global _watch_seen
    seen = _watch_seen or _watch_load_state()
    global watch_running
    watch_running = True
    while watch_running:
        try:
            handle = watch_handle_var.get().strip()
            # Normaliser les handles de type "@nom" en URL de profil TikTok
            try:
                if handle.startswith('@'):
                    handle = f"https://www.tiktok.com/{handle}"
            except Exception:
                pass
            if not handle:
                break
            # obtenir une liste de vidéos depuis le profil via yt-dlp (playlist)
            urls = []
            try:
                import yt_dlp
                ydl_opts = {'extract_flat': True, 'skip_download': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(handle, download=False)
                    entries = info.get('entries') or []
                    for e in entries:
                        u = e.get('url') or e.get('webpage_url')
                        if u:
                            urls.append(u)
            except Exception as e:
                log('error', f"Watch: impossible de lister {handle}: {e}")

            # Appliquer filtres et quota
            inc_kw = _split_csv(watch_inc_kw_var.get())
            exc_kw = _split_csv(watch_exc_kw_var.get())
            try:
                min_d = int(watch_min_dur_var.get() or '0')
                max_d = int(watch_max_dur_var.get() or '0')
            except Exception:
                min_d, max_d = 0, 0
            try:
                quota = int(watch_quota_var.get() or '0')
            except Exception:
                quota = 0

            added = 0
            for u in urls:
                if not watch_running:
                    break
                if u in seen:
                    continue
                # récupérer meta et filtrer
                try:
                    meta = fetch_tiktok_metadata(u) or {}
                    if _filters_ok(meta or {}, inc_kw, exc_kw, min_d, max_d):
                        # Préparer description + tags depuis hashtags
                        desc = (meta.get('description') or '').strip()
                        hashtags = meta.get('hashtags') or []
                        # Conformer les tags (liste de str, sans #, uniques)
                        norm_tags = []
                        seen_t = set()
                        for t in hashtags:
                            tt = (t or '').strip().lstrip('#')
                            if not tt:
                                continue
                            k = tt.lower()
                            if k in seen_t:
                                continue
                            seen_t.add(k)
                            norm_tags.append(tt)
                        norm_tags = _sanitize_tags_500(norm_tags) if norm_tags else []
                        queue_add_item(u, meta.get('title') or '', description=desc, tags=norm_tags)
                        seen.add(u)
                        _watch_seen = seen
                        _watch_save_state()
                        added += 1
                        if quota and added >= quota:
                            break
                except Exception as e:
                    log('error', f"Watch: meta échouée {u}: {e}")

            # marquer le dernier poll
            try:
                watch_last_poll_var.set(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                _watch_save_state()
            except Exception:
                pass

            # dormir jusqu'au prochain poll
            try:
                minutes = float(watch_interval_var.get() or '10')
            except Exception:
                minutes = 10.0
            for _ in range(int(minutes * 60 / 1)):
                if not watch_running:
                    break
                _time.sleep(1)
        except Exception as e:
            log('error', f"Watch: erreur: {e}")
        # boucle continue tant que watch_running reste True
    watch_running = False

def on_watch_start():
    if not watch_running:
        threading.Thread(target=_watch_worker, daemon=True).start()
        set_status('Surveillance démarrée')

def on_watch_stop():
    global watch_running
    watch_running = False
    set_status('Surveillance arrêtée')

# Charger état de surveillance au démarrage
root.after(0, lambda: (_watch_seen.update(_watch_load_state())))

tb.Button(watch_frame, text='Démarrer', bootstyle=SUCCESS, command=on_watch_start).grid(row=0, column=4, padx=(10,0))
tb.Button(watch_frame, text='Arrêter', bootstyle=DANGER, command=on_watch_stop).grid(row=0, column=5, padx=(6,0))

watch_frame.columnconfigure(1, weight=1)
watch_frame.columnconfigure(3, weight=0)

# Dernier poll & autostart
watch_last_poll_var = tk.StringVar(value='—')
tb.Label(watch_frame, text='Dernier poll:').grid(row=4, column=0, sticky=E, pady=(4,0))
watch_last_poll_lbl = tb.Label(watch_frame, textvariable=watch_last_poll_var, bootstyle=SECONDARY)
watch_last_poll_lbl.grid(row=4, column=1, sticky=W, pady=(4,0))

watch_autostart_var = tk.BooleanVar(value=False)
tb.Checkbutton(watch_frame, text='Démarrer au lancement', variable=watch_autostart_var, bootstyle=SECONDARY).grid(row=4, column=2, columnspan=2, sticky=W, pady=(4,0))

def _watch_save_prefs():
    try:
        # save_settings réécrit depuis les variables globales déjà liées
        save_settings()
    except Exception:
        pass
watch_autostart_var.trace_add('write', lambda *_: _watch_save_prefs())

# Charger préférence d'autostart et démarrer si activé
try:
    if settings.get('watchAutostart') is not None:
        watch_autostart_var.set(bool(settings.get('watchAutostart')))
    if watch_autostart_var.get():
        root.after(400, on_watch_start)
except Exception:
    pass


# Worker de file d'attente
queue_running = False
queue_paused = False
pause_after_n_var = tk.BooleanVar(value=False)
pause_after_n_value = tk.StringVar(value='0')
_processed_in_run = 0

def _update_item_progress(iid, d_pct=None, u_pct=None, status=None, result=None):
    try:
        cur = queue_tree.item(iid, 'values')
        url, title, st, d, u, res = cur
        if d_pct is not None:
            d = f"{d_pct:.0f}%"
        if u_pct is not None:
            u = f"{u_pct:.0f}%"
        if status is not None:
            st = status
        if result is not None:
            res = result
        queue_tree.item(iid, values=(url, title, st, d, u, res))
        for it in queue_items:
            if it['iid'] == iid:
                try:
                    it['status'] = st
                    it['d_pct'] = int(d.replace('%','')) if isinstance(d, str) else it.get('d_pct', 0)
                    it['u_pct'] = int(u.replace('%','')) if isinstance(u, str) else it.get('u_pct', 0)
                    it['result'] = res
                except Exception:
                    pass
                break
        _queue_save()
    except Exception:
        pass

def _process_one_item(item):
    # Alimente les callbacks de progression pour l'item
    def _dl_prog(p):
        root.after(0, _update_item_progress, item['iid'], p, None, 'téléchargement', None)
        set_download_progress(p)
    def _ul_prog(p):
        root.after(0, _update_item_progress, item['iid'], None, p, 'upload', None)
        set_upload_progress(p)

    # Remplit les champs UI principaux avant de réutiliser process core
    entry_url.delete(0, tk.END)
    entry_url.insert(0, item['url'])
    if item.get('title'):
        entry_title.delete(0, tk.END)
        entry_title.insert(0, item['title'])

    # Reprise de la logique de process mais en mode “inline” pour contrôler callbacks
    url = item['url']
    title = entry_title.get().strip()
    # Description: préférer celle de l'item si fournie par le watcher
    item_desc = (item.get('description') or '').strip()
    description = item_desc if item_desc else text_desc.get("1.0", tk.END).strip()
    privacy = privacy_var.get()

    # Reconstruire advanced minimal depuis l'UI courante
    # Tags: fusionner ceux de l'item avec ceux de l'UI
    tags_input = tags_var.get().strip()
    ui_tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
    item_tags = item.get('tags') or []
    merged_tags = []
    seen_tags = set()
    for t in (list(ui_tags) + list(item_tags)):
        tt = (t or '').strip().lstrip('#')
        if not tt:
            continue
        k = tt.lower()
        if k in seen_tags:
            continue
        seen_tags.add(k)
        merged_tags.append(tt)
    tags = _sanitize_tags_500(merged_tags) if merged_tags else None
    cat_name = category_var.get()
    category_id = YOUTUBE_CATEGORIES.get(cat_name) or DEFAULT_CATEGORY_ID
    lang_name = language_var.get()
    default_lang = LANGUAGES.get(lang_name)
    made_for_kids = made_for_kids_var.get()
    license_name = license_var.get()
    license_val = LICENSES.get(license_name)
    draft = draft_var.get()
    publish_at_raw = schedule_var.get().strip()
    rec_date_raw = recording_date_var.get().strip()
    publish_at = parse_rfc3339(publish_at_raw) if publish_at_raw else None
    rec_date = parse_rfc3339(rec_date_raw) if rec_date_raw else None
    loc_desc = location_desc_var.get().strip() or None
    lat_val = latitude_var.get().strip() or None
    lon_val = longitude_var.get().strip() or None
    playlists_input = playlists_var.get().strip()
    playlists = [p.strip() for p in playlists_input.split(",") if p.strip()] if playlists_input else []
    adv = {
        "tags": tags,
        "categoryId": category_id,
        "defaultLanguage": default_lang,
        "madeForKids": made_for_kids,
        "license": license_val,
        "draft": draft,
        "publishAt": publish_at,
        "recordingDate": rec_date,
        "locationDescription": loc_desc,
        "latitude": lat_val,
        "longitude": lon_val,
        "playlists": playlists,
        "timeout": (timeout_var.get().strip() if 'timeout_var' in globals() else ''),
        "proxy": (proxy_var.get().strip() if 'proxy_var' in globals() else ''),
        "uploadChunkMB": (upload_chunk_mb_var.get().strip() if 'upload_chunk_mb_var' in globals() else ''),
        "uploadMaxRetries": (upload_retries_var.get().strip() if 'upload_retries_var' in globals() else ''),
    }

    # Télécharger
    set_status("Téléchargement (queue)…")
    try:
        video_file, info = download_tiktok_with_info(
            url,
            on_progress=_dl_prog,
            proxy=(adv.get('proxy') or '').strip() or None,
            timeout=(adv.get('timeout') or '').strip() or None,
        )
    except Exception as e:
        root.after(0, _update_item_progress, item['iid'], None, None, 'erreur', str(e))
        return

    # Upload
    set_status("Upload (queue)…")
    try:
        vid = upload_to_youtube(video_file, title, description, privacy, on_progress=_ul_prog, advanced=adv)
        apply_post_upload_settings(vid, adv)
        root.after(0, _update_item_progress, item['iid'], None, 100.0, 'terminé', vid)
        last_video_id.set(vid or "")
    except Exception as e:
        root.after(0, _update_item_progress, item['iid'], None, None, 'erreur', str(e))
    finally:
        try:
            if video_file and os.path.exists(video_file):
                os.remove(video_file)
                temp_dir = os.path.dirname(video_file)
                if os.path.isdir(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        except Exception:
            pass

def _queue_worker():
    global queue_running
    queue_running = True
    global _processed_in_run, queue_paused
    _processed_in_run = 0
    for item in list(queue_items):
        if not queue_running:
            break
        # pause
        while queue_paused and queue_running:
            time.sleep(0.2)
        # sauter les terminés/erreur déjà marqués
        vals = queue_tree.item(item['iid'], 'values')
        # Ne pas relancer les éléments 'terminé' (les erreurs seront rejouées par défaut)
        if vals and vals[2] in ('terminé',):
            continue
        root.after(0, _update_item_progress, item['iid'], 0.0, 0.0, 'en cours', None)
        _process_one_item(item)
        # Après chaque item traité, appliquer la pause automatique si activée
        try:
            if pause_after_n_var.get():
                try:
                    n = int((pause_after_n_value.get() or '0').strip())
                except Exception:
                    n = 0
                if n > 0:
                    _processed_in_run += 1
                    if _processed_in_run >= n:
                        queue_paused = True
                        _processed_in_run = 0
                        set_status(f'Queue en pause (quota {n} atteint)')
        except Exception:
            pass
    queue_running = False

def on_queue_start():
    global _processed_in_run
    _processed_in_run = 0
    if not queue_running:
        threading.Thread(target=_queue_worker, daemon=True).start()

def on_queue_pause_resume():
    global queue_paused
    queue_paused = not queue_paused
    # Si on reprend, réinitialiser le compteur courant
    global _processed_in_run
    if not queue_paused:
        _processed_in_run = 0
    set_status('Queue en pause' if queue_paused else 'Queue en cours')

def on_queue_clear_done():
    for iid in queue_tree.get_children():
        vals = queue_tree.item(iid, 'values')
        if vals and vals[2] == 'terminé':
            queue_tree.delete(iid)
    # sync modèle
    remaining = []
    for it in queue_items:
        try:
            vals = queue_tree.item(it['iid'], 'values')
            if vals:
                remaining.append(it)
        except Exception:
            pass
    queue_items[:] = remaining

def on_queue_resume_errors():
    """Remettre uniquement les items en erreur à 'en attente' et relancer si nécessaire."""
    changed = 0
    try:
        for it in queue_items:
            st = (it.get('status') or '')
            if st == 'erreur':
                it['status'] = 'en attente'
                try:
                    queue_tree.item(it['iid'], values=(it.get('url',''), it.get('title',''), 'en attente', f"{it.get('d_pct',0)}%", f"{it.get('u_pct',0)}%", it.get('result','')))
                except Exception:
                    pass
                changed += 1
    except Exception:
        pass
    if changed:
        _queue_save()
        set_status(f"Erreurs remises en attente: {changed}")
    # relancer si non démarré, sinon juste résumer
    global queue_running, queue_paused, _processed_in_run
    if not queue_running:
        _processed_in_run = 0
        on_queue_start()
    else:
        queue_paused = False
        _processed_in_run = 0
        set_status('Queue reprise (erreurs)')

tb.Button(queue_toolbar, text='Démarrer', bootstyle=SUCCESS, command=on_queue_start).pack(side=RIGHT)
tb.Button(queue_toolbar, text='Pause/Resume', bootstyle=WARNING, command=on_queue_pause_resume).pack(side=RIGHT, padx=(6,0))
tb.Button(queue_toolbar, text='Vider terminés', bootstyle=SECONDARY, command=on_queue_clear_done).pack(side=RIGHT, padx=(6,0))
tb.Button(queue_toolbar, text='Reprendre erreurs', bootstyle=INFO, command=on_queue_resume_errors).pack(side=RIGHT, padx=(6,0))

# Option "Pause après N vidéos"
pause_n_frame = tb.Frame(queue_toolbar)
pause_n_frame.pack(side=RIGHT, padx=(12,0))
tb.Checkbutton(pause_n_frame, text='Pause après', variable=pause_after_n_var, bootstyle=SECONDARY).pack(side=LEFT)
tb.Entry(pause_n_frame, textvariable=pause_after_n_value, width=4).pack(side=LEFT, padx=(4,0))
tb.Label(pause_n_frame, text='vidéo(s)').pack(side=LEFT, padx=(4,0))

# Charger état de "Pause après N" depuis settings (après création des widgets)
try:
    if settings.get('pauseAfterNEnabled') is not None:
        pause_after_n_var.set(bool(settings.get('pauseAfterNEnabled')))
    if settings.get('pauseAfterNValue') is not None:
        pause_after_n_value.set(str(settings.get('pauseAfterNValue')))
except Exception:
    pass

# Sauvegarder automatiquement les changements de l'option "Pause après N"
def _bind_pause_after_n_save(*_):
    try:
        save_settings()
    except Exception:
        pass
try:
    pause_after_n_var.trace_add('write', _bind_pause_after_n_save)
    pause_after_n_value.trace_add('write', _bind_pause_after_n_save)
except Exception:
    pass

# Actions
actions = tb.Frame(container)
actions.pack(fill=X, pady=5)

btn_start = tb.Button(actions, text="▶ Lancer", bootstyle=SUCCESS, command=process)
btn_start.pack(side=RIGHT, padx=6)
btn_cancel = tb.Button(actions, text="✖ Annuler", bootstyle=DANGER, state=DISABLED, command=cancel_action)
btn_cancel.pack(side=RIGHT)

# Boutons post-upload
last_video_id = tk.StringVar(value="")

def open_video():
    vid = last_video_id.get().strip()
    if not vid:
        return
    url = f"https://youtu.be/{vid}"
    try:
        webbrowser.open(url)
    except Exception:
        try:
            subprocess.Popen(['xdg-open', url])
        except Exception:
            messagebox.showerror('Erreur', "Impossible d’ouvrir le navigateur")

def copy_video_id():
    vid = last_video_id.get().strip()
    if not vid:
        return
    try:
        root.clipboard_clear()
        root.clipboard_append(vid)
        set_status('ID vidéo copié')
    except Exception:
        messagebox.showerror('Erreur', "Impossible de copier l’ID")

btn_open_video = tb.Button(actions, text="Ouvrir vidéo", bootstyle=SECONDARY, state=DISABLED, command=open_video)
btn_open_video.pack(side=LEFT)
btn_copy_id = tb.Button(actions, text="Copier ID", bootstyle=SECONDARY, state=DISABLED, command=copy_video_id)
btn_copy_id.pack(side=LEFT, padx=(6,0))

status_label = tb.Label(container, text="Prêt.")
status_label.pack(fill=X, pady=(6, 0))

# Journal des événements
journal = tb.Labelframe(container, text="Journal", bootstyle=SECONDARY)
journal.pack(fill=BOTH, expand=YES, pady=10)

log_text = ScrolledText(journal, height=10, wrap=tk.WORD, state='disabled')
log_text.pack(fill=BOTH, expand=YES, padx=4, pady=6)

def copy_logs():
    try:
        content = ''.join(_log_history)
        root.clipboard_clear()
        root.clipboard_append(content)
        set_status('Logs copiés dans le presse-papiers')
    except Exception:
        messagebox.showerror('Erreur', 'Impossible de copier les logs')

btns = tb.Frame(journal)
btns.pack(fill=X)
tb.Button(btns, text='Copier les logs', bootstyle=INFO, command=copy_logs).pack(side=RIGHT)

def copy_log_path():
    try:
        root.clipboard_clear()
        root.clipboard_append(str(LOG_FILE))
        set_status('Chemin du log copié')
    except Exception:
        messagebox.showerror('Erreur', 'Impossible de copier le chemin du log')

tb.Button(btns, text='Copier chemin log', bootstyle=SECONDARY, command=copy_log_path).pack(side=RIGHT, padx=6)

def open_logs_dir():
    try:
        subprocess.Popen(['xdg-open', str(CONFIG_DIR)])
    except Exception:
        messagebox.showerror('Erreur', 'Impossible d’ouvrir le dossier des logs')

tb.Button(btns, text='Ouvrir dossier logs', bootstyle=INFO, command=open_logs_dir).pack(side=RIGHT, padx=6)

def purge_temp_files():
    import tempfile as _tf
    tmpdir = _tf.gettempdir()
    removed = 0
    try:
        for name in os.listdir(tmpdir):
            if name.startswith('t2y_'):
                p = os.path.join(tmpdir, name)
                try:
                    if os.path.isdir(p):
                        # supprimer récursivement
                        shutil.rmtree(p, ignore_errors=True)
                        removed += 1
                    elif os.path.isfile(p):
                        os.remove(p)
                        removed += 1
                except Exception:
                    pass
        set_status(f"Temporaires purgés: {removed}")
        log('info', f"Purge temporaires: {removed} élément(s)")
    except Exception as e:
        messagebox.showerror('Erreur', f"Échec purge temporaires: {e}")

tb.Button(btns, text='Purger temporaires', bootstyle=DANGER, command=purge_temp_files).pack(side=RIGHT, padx=6)

# Export diagnostic (archive ZIP)
def export_diagnostics():
    try:
        import zipfile, io, platform, sys, importlib.metadata as md
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_name = f"t2y_diagnostics_{ts}.zip"
        dest = filedialog.asksaveasfilename(
            title='Exporter diagnostic',
            defaultextension='.zip',
            filetypes=[('Archive ZIP', '*.zip')],
            initialfile=default_name
        )
        if not dest:
            return

        # Collecte d'infos textuelles
        info_lines = []
        info_lines.append(f"Datetime: {datetime.now().isoformat()}")
        info_lines.append(f"OS: {platform.platform()}")
        info_lines.append(f"Python: {sys.version}")
        try:
            info_lines.append(f"ttkbootstrap: {md.version('ttkbootstrap')}")
        except Exception:
            pass
        for pkg in ['yt-dlp', 'google-api-python-client', 'google-auth-oauthlib', 'google-auth']:
            try:
                info_lines.append(f"{pkg}: {md.version(pkg)}")
            except Exception:
                pass
        # Proxies
        try:
            info_lines.append(f"HTTP_PROXY: {os.environ.get('HTTP_PROXY','')}")
            info_lines.append(f"HTTPS_PROXY: {os.environ.get('HTTPS_PROXY','')}")
        except Exception:
            pass
        # ffmpeg version si dispo
        ff_info = ''
        try:
            if shutil.which('ffmpeg'):
                r = subprocess.run(['ffmpeg','-version'], capture_output=True, text=True, timeout=3)
                ff_info = r.stdout.strip() or r.stderr.strip()
        except Exception:
            pass

        # Packages installés (façon freeze light)
        try:
            dists = sorted([(d.metadata['Name'] or d.metadata.get('name') or d.metadata['Summary'] or str(d)) for d in md.distributions()])
            # Note: on préfère une liste versionnée simple
            freeze = []
            for d in md.distributions():
                try:
                    freeze.append(f"{d.metadata['Name']}=={d.version}")
                except Exception:
                    pass
            freeze.sort()
            freeze_txt = "\n".join(freeze)
        except Exception:
            freeze_txt = ''

        with zipfile.ZipFile(dest, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            # Infos principales
            z.writestr('environment/info.txt', "\n".join(info_lines))
            if ff_info:
                z.writestr('environment/ffmpeg.txt', ff_info)
            if freeze_txt:
                z.writestr('environment/pip_freeze.txt', freeze_txt)

            # Fichiers de config/logs
            def _safe_add(path, arcname):
                try:
                    if path and os.path.exists(path):
                        z.write(path, arcname)
                except Exception:
                    pass

            _safe_add(str(LOG_FILE), 'logs/t2y.log')
            _safe_add(str(SETTINGS_FILE), 'config/settings.json')
            try:
                from t2y.constants import PROFILES_FILE as _P, WATCH_STATE_FILE as _W, UPLOADS_DB as _U
                _safe_add(str(_P), 'config/profiles.json')
                _safe_add(str(_W), 'config/watch_state.json')
                _safe_add(str(_U), 'config/uploads_db.json')
            except Exception:
                pass
            # queue
            try:
                from t2y.config import CONFIG_DIR as _CFG
                qf = _CFG / 'queue.json'
                _safe_add(str(qf), 'config/queue.json')
            except Exception:
                pass
            # requirements
            try:
                req = Path(__file__).resolve().parent.parent / 'requirements.txt'
                _safe_add(str(req), 'project/requirements.txt')
            except Exception:
                pass

        set_status(f'Diagnostic exporté → {dest}')
        log('info', f'Diagnostic exporté: {dest}')
        try:
            messagebox.showinfo('Diagnostic', f'Archive créée:\n{dest}')
        except Exception:
            pass
    except Exception as e:
        messagebox.showerror('Erreur', f"Export diagnostic échoué: {e}")

tb.Button(btns, text='Exporter diagnostic', bootstyle=PRIMARY, command=export_diagnostics).pack(side=RIGHT, padx=6)

# Sélecteur de niveau de log
lvl_frame = tb.Frame(journal)
lvl_frame.pack(fill=X, pady=(4, 0))
tb.Label(lvl_frame, text='Niveau de log:').pack(side=LEFT)
level_var = tk.StringVar(value=settings.get('logLevel', get_log_level()))

def on_level_change(event=None):
    set_log_level(level_var.get())
    log('info', f"Niveau de log réglé sur {get_log_level()}")
    save_settings()

level_combo = tb.Combobox(lvl_frame, textvariable=level_var, values=['DEBUG', 'INFO', 'ERROR'], width=8, state='readonly')
level_combo.bind('<<ComboboxSelected>>', on_level_change)
level_combo.pack(side=LEFT, padx=(6, 0))

# Config couleurs de logs
try:
    log_text.tag_config('INFO', foreground='#4dd0e1')  # cyan clair
    log_text.tag_config('ERROR', foreground='#ff5252')  # rouge
except Exception:
    pass

form.columnconfigure(1, weight=1)
form.rowconfigure(2, weight=1)

# Tooltips (attachés après construction complète de l'UI)
def _setup_tooltips():
    try:
        attach_tooltip(entry_url, "Collez une URL TikTok (ex: https://www.tiktok.com/@user/video/…)")
    except Exception:
        pass
    try:
        attach_tooltip(prefill_btn, "Récupère titre, description et miniature depuis TikTok")
    except Exception:
        pass
    try:
        attach_tooltip(download_pb, "Progression du téléchargement")
        attach_tooltip(upload_pb, "Progression de l’upload YouTube")
    except Exception:
        pass
    try:
        attach_tooltip(privacy_combo, "Visibilité initiale de la vidéo")
    except Exception:
        pass
    try:
        attach_tooltip(tags_entry, "Séparez les tags par des virgules")
    except Exception:
        pass
    try:
        attach_tooltip(recording_date_entry, "Ex: 2024-08-25T14:33:00Z (UTC)")
        attach_tooltip(schedule_entry, "Planifier publication: 2024-08-25T14:33:00Z (UTC)")
        attach_tooltip(playlists_entry, "IDs de playlists séparés par des virgules")
    except Exception:
        pass

root.after(200, _setup_tooltips)


# Validation URL et activation bouton
def validate_inputs(*_):
    url = url_var.get().strip()
    title = title_var.get().strip()
    ok_url = is_valid_tiktok_url(url)
    ok_title = len(title) > 0
    if ok_url:
        url_valid_label.configure(text="URL valide", bootstyle=SUCCESS)
    else:
        url_valid_label.configure(text="URL invalide", bootstyle=DANGER)
    btn_start.configure(state=(NORMAL if ok_url and ok_title else DISABLED))

url_var.trace_add('write', validate_inputs)
title_var.trace_add('write', validate_inputs)
root.after(0, validate_inputs)

# Validation visuelle des dates RFC3339 (en direct)
def validate_dates(*_):
    try:
        val = recording_date_var.get().strip()
        if not val:
            rec_date_status.configure(text="", bootstyle=SECONDARY)
        else:
            ok = True if parse_rfc3339(val) else False
            if ok:
                rec_date_status.configure(text="OK", bootstyle=SUCCESS)
            else:
                rec_date_status.configure(text="Invalide", bootstyle=DANGER)
    except Exception:
        rec_date_status.configure(text="Invalide", bootstyle=DANGER)
    try:
        val = schedule_var.get().strip()
        if not val:
            schedule_status.configure(text="", bootstyle=SECONDARY)
        else:
            ok = True if parse_rfc3339(val) else False
            if ok:
                schedule_status.configure(text="OK", bootstyle=SUCCESS)
            else:
                schedule_status.configure(text="Invalide", bootstyle=DANGER)
    except Exception:
        schedule_status.configure(text="Invalide", bootstyle=DANGER)

recording_date_var.trace_add('write', validate_dates)
schedule_var.trace_add('write', validate_dates)
root.after(0, validate_dates)

def _on_close():
    save_settings()
    try:
        root.destroy()
    except Exception:
        os._exit(0)

root.protocol('WM_DELETE_WINDOW', _on_close)

# Raccourcis clavier: Entrée pour lancer si possible
def attempt_start(event=None):
    validate_inputs()
    if str(btn_start['state']) == 'normal':
        process()

entry_url.bind('<Return>', attempt_start)
entry_title.bind('<Return>', attempt_start)
root.bind('<Control-Return>', attempt_start)

# Raccourcis utiles
try:
    root.bind('<Control-l>', lambda e: attempt_start())
    root.bind('<Control-L>', lambda e: attempt_start())
    root.bind('<Control-Shift-c>', lambda e: copy_logs())
    root.bind('<Control-Shift-C>', lambda e: copy_logs())
    root.bind('<Control-o>', lambda e: open_logs_dir())
    root.bind('<Control-O>', lambda e: open_logs_dir())
    root.bind('<Control-p>', lambda e: prefill_from_tiktok())
    root.bind('<Control-P>', lambda e: prefill_from_tiktok())
except Exception:
    pass

# Drag & drop optionnel (si tkinterdnd2 dispo)
try:
    from tkinterdnd2 import DND_TEXT  # type: ignore
    entry_url.drop_target_register(DND_TEXT)
    def _on_drop(event):
        data = event.data or ''
        data = data.strip().strip('{}')
        url_var.set(data)
        validate_inputs()
    entry_url.dnd_bind('<<Drop>>', _on_drop)
    attach_tooltip(entry_url, "Glissez-déposez une URL TikTok ici")
except Exception:
    pass

root.mainloop()
