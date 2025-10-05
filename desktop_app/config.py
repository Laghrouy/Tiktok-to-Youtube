"""
Configuration et paramètres pour l'application de bureau
"""

import os
import json
from pathlib import Path

# Répertoires de configuration
APP_DIR = Path(__file__).parent
CONFIG_DIR = Path.home() / '.tiktok-to-youtube-desktop'
CONFIG_FILE = CONFIG_DIR / 'config.json'

# Configuration par défaut
DEFAULT_CONFIG = {
    'appearance': {
        'theme': 'dark',
        'accent_color': '#8b5cf6',
        'font_family': 'Segoe UI',
        'font_size': 14,
        'animations_enabled': True,
        'transparency_enabled': True
    },
    'behavior': {
        'auto_fetch_metadata': True,
        'auto_detect_shorts': True,
        'remember_last_settings': True,
        'minimize_to_tray': False,
        'close_to_tray': False
    },
    'processing': {
        'default_privacy': 'public',
        'default_category': 'Entertainment',
        'default_language': 'Français (fr)',
        'auto_normalize_audio': False,
        'auto_remux': True,
        'concurrent_uploads': 1
    },
    'window': {
        'width': 1200,
        'height': 800,
        'x': -1,  # -1 = centré
        'y': -1,  # -1 = centré
        'maximized': False,
        'remember_size': True
    },
    'recent': {
        'urls': [],
        'titles': [],
        'descriptions': [],
        'max_items': 10
    }
}

class Config:
    """Gestionnaire de configuration de l'application"""
    
    def __init__(self):
        self.config = DEFAULT_CONFIG.copy()
        self.load()
    
    def load(self):
        """Charge la configuration depuis le fichier"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self._merge_config(saved_config)
        except Exception as e:
            print(f"Erreur lors du chargement de la configuration: {e}")
    
    def save(self):
        """Sauvegarde la configuration"""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de la configuration: {e}")
    
    def _merge_config(self, saved_config):
        """Fusionne la configuration sauvegardée avec la configuration par défaut"""
        def merge_dict(default, saved):
            for key, value in saved.items():
                if key in default:
                    if isinstance(value, dict) and isinstance(default[key], dict):
                        merge_dict(default[key], value)
                    else:
                        default[key] = value
        
        merge_dict(self.config, saved_config)
    
    def get(self, section, key=None, default=None):
        """Récupère une valeur de configuration"""
        if key is None:
            return self.config.get(section, default)
        return self.config.get(section, {}).get(key, default)
    
    def set(self, section, key, value):
        """Définit une valeur de configuration"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
    
    def add_recent_url(self, url):
        """Ajoute une URL à l'historique récent"""
        recent_urls = self.config['recent']['urls']
        if url in recent_urls:
            recent_urls.remove(url)
        recent_urls.insert(0, url)
        recent_urls = recent_urls[:self.config['recent']['max_items']]
        self.config['recent']['urls'] = recent_urls
        self.save()
    
    def add_recent_title(self, title):
        """Ajoute un titre à l'historique récent"""
        recent_titles = self.config['recent']['titles']
        if title in recent_titles:
            recent_titles.remove(title)
        recent_titles.insert(0, title)
        recent_titles = recent_titles[:self.config['recent']['max_items']]
        self.config['recent']['titles'] = recent_titles
        self.save()
    
    def get_recent_urls(self):
        """Récupère les URLs récentes"""
        return self.config['recent']['urls']
    
    def get_recent_titles(self):
        """Récupère les titres récents"""
        return self.config['recent']['titles']

# Instance globale de configuration
config = Config()

# Thèmes disponibles
THEMES = {
    'dark': {
        'name': 'Sombre',
        'background': '#0a0a0a',
        'surface': '#1a1a1a',
        'primary': '#8b5cf6',
        'secondary': '#06b6d4',
        'accent': '#ec4899',
        'text_primary': '#ffffff',
        'text_secondary': '#a1a1aa'
    },
    'midnight': {
        'name': 'Minuit',
        'background': '#0f0f23',
        'surface': '#1a1a3e',
        'primary': '#7c3aed',
        'secondary': '#3b82f6',
        'accent': '#f59e0b',
        'text_primary': '#ffffff',
        'text_secondary': '#94a3b8'
    },
    'cyberpunk': {
        'name': 'Cyberpunk',
        'background': '#0d1117',
        'surface': '#161b22',
        'primary': '#ff6b9d',
        'secondary': '#00d9ff',
        'accent': '#ffff00',
        'text_primary': '#ffffff',
        'text_secondary': '#8b949e'
    },
    'ocean': {
        'name': 'Océan',
        'background': '#0a192f',
        'surface': '#112240',
        'primary': '#64ffda',
        'secondary': '#00bcd4',
        'accent': '#ff6b6b',
        'text_primary': '#ffffff',
        'text_secondary': '#8892b0'
    }
}

def get_theme(theme_name='dark'):
    """Récupère un thème par son nom"""
    return THEMES.get(theme_name, THEMES['dark'])

def get_available_themes():
    """Récupère la liste des thèmes disponibles"""
    return [(key, theme['name']) for key, theme in THEMES.items()]