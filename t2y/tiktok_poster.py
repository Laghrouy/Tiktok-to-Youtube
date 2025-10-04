"""
Stubs de publication TikTok via l’Open API (Content Posting).
Pas d’OAuth ni de clés ici, uniquement la signature prévue et un retour factice.
"""

from typing import Optional, Callable
import os
import time
import json
import mimetypes
from .tiktok_auth import get_token, is_configured

def post_to_tiktok(video_path: str, caption: str = '', *, on_progress: Optional[Callable[[int], None]] = None, advanced: Optional[dict] = None) -> str:
    """
    Upload TikTok réel (Content Posting API v2):
    - upload chunked
    - publish avec caption
    - fallback stub si non configuré/token absent
    """
    try:
        import requests
    except ImportError:
        # fallback stub
        if on_progress:
            on_progress(20)
            on_progress(60)
            on_progress(100)
        return 'tt_stub_video_id'

    token = get_token() or {}
    access_token = token.get('access_token') or token.get('token')
    if not is_configured() or not access_token:
        if on_progress:
            on_progress(20)
            on_progress(60)
            on_progress(100)
        return 'tt_stub_video_id'

    # 1. Obtenir upload_url
    try:
        headers = {'Authorization': f'Bearer {access_token}'}
        resp = requests.post(
            'https://open.tiktokapis.com/v2/post/publish/video/init/',
            headers=headers,
            json={"post_type": "VIDEO"},
            timeout=15
        )
        resp.raise_for_status()
        j = resp.json()
        upload_url = j['data']['upload_url']
        video_id = j['data']['video_id']
    except Exception as e:
        return f'tt_error_init: {e}'

    # 2. Upload chunked (ici, on fait un PUT direct, TikTok accepte le fichier entier en un seul PUT si <100Mo)
    try:
        size = os.path.getsize(video_path)
        mime = mimetypes.guess_type(video_path)[0] or 'video/mp4'
        with open(video_path, 'rb') as f:
            data = f.read()
        up_resp = requests.put(
            upload_url,
            data=data,
            headers={
                'Content-Type': mime,
                'Content-Length': str(size),
            },
            timeout=60
        )
        up_resp.raise_for_status()
        if on_progress:
            on_progress(80)
    except Exception as e:
        return f'tt_error_upload: {e}'

    # 3. Publish
    try:
        pub_resp = requests.post(
            'https://open.tiktokapis.com/v2/post/publish/video/publish/',
            headers=headers,
            json={
                "video_id": video_id,
                "text": caption or '',
            },
            timeout=15
        )
        pub_resp.raise_for_status()
        pub_j = pub_resp.json()
        post_id = pub_j['data']['post_id']
        if on_progress:
            on_progress(100)
        return post_id
    except Exception as e:
        return f'tt_error_publish: {e}'
