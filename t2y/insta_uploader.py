"""
Stubs d’upload Instagram via Instagram Graph API.
Ce module ne contient PAS de clés ni d’OAuth. Il expose juste des fonctions
avec la même signature que l’uploader YouTube pour préparer l’intégration.
"""
from typing import Optional, Callable

def upload_to_instagram(video_path: str, caption: str = '', *, on_progress: Optional[Callable[[int], None]] = None, advanced: Optional[dict] = None) -> str:
    """Stub d’upload. Ne fait rien et renvoie une valeur de test.
    Implémentation future:
    - upload via URL publique (ou tunnel) vers /media (creation container)
    - polling de status, puis publication via /media_publish
    - gestion des erreurs/limites API
    """
    if on_progress:
        on_progress(10)
        on_progress(50)
        on_progress(100)
    return 'ig_stub_post_id'
