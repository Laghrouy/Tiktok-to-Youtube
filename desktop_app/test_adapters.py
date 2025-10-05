#!/usr/bin/env python3
"""
Test rapide des adaptateurs TikTok to YouTube
"""

import sys
from pathlib import Path

# Configuration du path
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_adapters():
    """Test rapide des adaptateurs"""
    print("🧪 Test des adaptateurs TikTok to YouTube")
    print("=" * 50)
    
    try:
        from adapters import TikTokDownloader, YouTubeUploader, MetadataProcessor
        print("✅ Import des adaptateurs réussi")
        
        # Test instanciation
        downloader = TikTokDownloader()
        uploader = YouTubeUploader()
        processor = MetadataProcessor()
        print("✅ Instanciation des classes réussie")
        
        # Test configuration
        config = {
            'title': 'Test Video',
            'description': 'Video de test',
            'tags': ['test', 'demo'],
            'privacy': 'private'
        }
        
        metadata = processor.process('/fake/path', config)
        print(f"✅ Traitement métadonnées: {metadata['title']}")
        
        print("\n🎉 Tous les tests réussis !")
        print("✅ Les adaptateurs sont fonctionnels")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False

if __name__ == "__main__":
    success = test_adapters()
    sys.exit(0 if success else 1)