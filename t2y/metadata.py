def fetch_tiktok_metadata(url: str) -> dict:
    # Stub: renvoie des métadonnées minimales
    return {
        'title': 'TikTok video',
        'description': '',
        'hashtags': [],
        'duration': 30,
    }
import yt_dlp
from typing import Optional, Dict, List
import re


def fetch_tiktok_metadata(url: str) -> Optional[Dict[str, str | List[str] | int]]:
    """Récupère les métadonnées principales d'une URL TikTok sans télécharger la vidéo.

    Retourne un dict avec: {
        'title': str | None,
        'description': str | None,
        'thumbnail': str | None,
        'hashtags': List[str] | [],
        'duration': int | None
    } ou None si échec.
    """
    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        if not info:
            return None
        # Récupérer hashtags: priorité aux tags fournis par yt-dlp, sinon extraire depuis la description
        yt_tags = info.get("tags") or []
        desc = info.get("description") or ""
        extracted = []
        try:
            # Capture les mots après # (alphanumériques/underscore, unicode)
            extracted = [m.group(1) for m in re.finditer(r"#(\w{1,60})", desc, flags=re.UNICODE)]
        except Exception:
            extracted = []
        # Nettoyer et dédoublonner en conservant l'ordre
        def _clean(tag: str) -> str:
            t = (tag or "").strip().lstrip('#').strip()
            # Filtrer tags trop longs
            return t[:60]

        seen = set()
        hashtags: List[str] = []
        for t in list(yt_tags) + extracted:
            ct = _clean(t)
            if ct and ct.lower() not in seen:
                seen.add(ct.lower())
                hashtags.append(ct)
        return {
            "title": info.get("title"),
            "description": info.get("description") or "",
            "thumbnail": info.get("thumbnail"),
            "hashtags": hashtags,
            "duration": info.get("duration") if isinstance(info.get("duration"), (int, float)) else None,
        }
    except Exception:
        return None
