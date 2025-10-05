"""
Adaptateurs de compatibilité pour l'application desktop
Fait le pont entre les fonctions t2y existantes et les classes attendues
"""

import os
import sys
from pathlib import Path

# Import des fonctions existantes
try:
    from t2y.downloader import download_tiktok, download_tiktok_with_info
    from t2y.uploader import upload_to_youtube
    from t2y.metadata import fetch_tiktok_metadata
    from t2y.logger import log
except ImportError as e:
    print(f"Erreur d'import des modules t2y: {e}")
    # Mode démo - classes vides
    def download_tiktok(*args, **kwargs):
        raise NotImplementedError("Modules t2y non disponibles")
    
    def download_tiktok_with_info(*args, **kwargs):
        raise NotImplementedError("Modules t2y non disponibles")
    
    def upload_to_youtube(*args, **kwargs):
        raise NotImplementedError("Modules t2y non disponibles")
    
    def fetch_tiktok_metadata(*args, **kwargs):
        return {}
    
    def log(*args, **kwargs):
        pass

class TikTokDownloader:
    """Adaptateur pour les fonctions de téléchargement TikTok"""
    
    def __init__(self, proxy=None, timeout=None):
        self.proxy = proxy
        self.timeout = timeout
        
    def download(self, url, on_progress=None):
        """
        Télécharge une vidéo TikTok
        
        Args:
            url (str): URL de la vidéo TikTok
            on_progress (callable): Callback de progression (optionnel)
            
        Returns:
            str: Chemin du fichier vidéo téléchargé
        """
        try:
            return download_tiktok(
                url=url,
                on_progress=on_progress,
                proxy=self.proxy,
                timeout=self.timeout
            )
        except Exception as e:
            log('error', f"Erreur de téléchargement: {e}")
            return None
            
    def download_with_info(self, url, on_progress=None):
        """
        Télécharge une vidéo TikTok avec informations
        
        Args:
            url (str): URL de la vidéo TikTok
            on_progress (callable): Callback de progression (optionnel)
            
        Returns:
            tuple: (chemin_fichier, info_dict)
        """
        try:
            return download_tiktok_with_info(
                url=url,
                on_progress=on_progress,
                proxy=self.proxy,
                timeout=self.timeout
            )
        except Exception as e:
            log('error', f"Erreur de téléchargement avec info: {e}")
            return None, {}

class YouTubeUploader:
    """Adaptateur pour les fonctions d'upload YouTube"""
    
    def __init__(self, profile=None):
        self.profile = profile
        
    def upload(self, video_path, metadata):
        """
        Upload une vidéo vers YouTube
        
        Args:
            video_path (str): Chemin du fichier vidéo
            metadata (dict): Métadonnées de la vidéo
            
        Returns:
            str: ID de la vidéo uploadée ou None en cas d'erreur
        """
        try:
            # Extraction des métadonnées
            title = metadata.get('title', 'Sans titre')
            description = metadata.get('description', '')
            privacy = metadata.get('privacy', 'public')
            
            # Options avancées
            advanced = {
                'tags': metadata.get('tags', []),
                'categoryId': metadata.get('category_id'),
                'defaultLanguage': metadata.get('language'),
                'madeForKids': metadata.get('made_for_kids', False),
                'license': metadata.get('license'),
                'timeout': metadata.get('timeout', 60),
                'proxy': metadata.get('proxy'),
                'profile': self.profile
            }
            
            # Upload
            return upload_to_youtube(
                video_path=video_path,
                title=title,
                description=description,
                privacy=privacy,
                on_progress=metadata.get('on_progress'),
                advanced=advanced
            )
            
        except Exception as e:
            log('error', f"Erreur d'upload: {e}")
            return None

class MetadataProcessor:
    """Adaptateur pour le traitement des métadonnées"""
    
    def __init__(self):
        pass
        
    def process(self, video_path, config):
        """
        Traite les métadonnées d'une vidéo
        
        Args:
            video_path (str): Chemin du fichier vidéo
            config (dict): Configuration des métadonnées
            
        Returns:
            dict: Métadonnées traitées
        """
        try:
            # Extraction des métadonnées depuis TikTok si URL fournie
            url = config.get('source_url')
            if url:
                tiktok_meta = fetch_tiktok_metadata(url)
            else:
                tiktok_meta = {}
                
            # Fusion avec la configuration utilisateur
            metadata = {
                'title': config.get('title') or tiktok_meta.get('title', 'Sans titre'),
                'description': config.get('description') or tiktok_meta.get('description', ''),
                'tags': config.get('tags') or tiktok_meta.get('hashtags', []),
                'category_id': config.get('category_id'),
                'language': config.get('language'),
                'made_for_kids': config.get('made_for_kids', False),
                'privacy': config.get('privacy', 'public'),
                'license': config.get('license'),
                'timeout': config.get('timeout'),
                'proxy': config.get('proxy'),
                'on_progress': config.get('on_progress')
            }
            
            return metadata
            
        except Exception as e:
            log('error', f"Erreur de traitement des métadonnées: {e}")
            return config