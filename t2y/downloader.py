import os, tempfile

try:
    import yt_dlp  # type: ignore
except Exception:
    yt_dlp = None


def download_tiktok_with_info(url: str, timeout=None, proxy=None, on_progress=None):
    """
    Télécharge une vidéo TikTok via yt_dlp.
    - Retourne (path, info) où path est le chemin du fichier vidéo téléchargé et info contient au moins 'duration' si disponible.
    - Lève une RuntimeError si yt_dlp est indisponible ou si le téléchargement échoue.
    """
    if yt_dlp is None:
        raise RuntimeError("yt_dlp non disponible pour le téléchargement")

    tmpdir = tempfile.mkdtemp(prefix='t2y_')
    outtmpl = os.path.join(tmpdir, '%(id)s.%(ext)s')

    def _hook(d):
        if on_progress and d.get('status') == 'downloading':
            try:
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                done = d.get('downloaded_bytes') or 0
                if total:
                    on_progress(int(max(0, min(100, done * 100.0 / total))))
            except Exception:
                pass
        if on_progress and d.get('status') == 'finished':
            try:
                on_progress(100)
            except Exception:
                pass

    ydl_opts = {
        'outtmpl': outtmpl,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': False,
        'socket_timeout': float(timeout or 30),
        'retries': 3,
        'progress_hooks': [_hook] if on_progress else [],
        # Essayer d’obtenir directement un MP4 pour éviter un merge (ffmpeg requis sinon)
        'format': 'mp4/best',
    }
    if proxy:
        ydl_opts['proxy'] = proxy

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        # Récupérer le chemin résultant
        path = None
        try:
            # requested_downloads est plus fiable si présent
            rd = info.get('requested_downloads') or []
            if rd:
                path = rd[0].get('filepath')
        except Exception:
            path = None
        if not path:
            try:
                path = ydl.prepare_filename(info)
            except Exception:
                path = None
        if not path or not os.path.exists(path):
            raise RuntimeError('Téléchargement TikTok échoué: fichier introuvable')
        # Extraire durée si possible
        duration = None
        try:
            duration = int(info.get('duration') or 0) or None
        except Exception:
            duration = None
        return path, ({'duration': duration} if duration else {})
