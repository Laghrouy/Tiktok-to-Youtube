"""
Application de bureau TikTok to YouTube
Version moderne avec interface PyQt6 et direction artistique sombre
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QFontDatabase

# Ajouter le chemin vers les modules t2y et le répertoire parent
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(current_dir)
sys.path.append(parent_dir)

from ui.main_window import MainWindow

def setup_application():
    """Configure l'application"""
    # Créer l'application
    app = QApplication(sys.argv)
    app.setApplicationName("TikTok to YouTube")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("TikTok2YouTube")
    
    # Configuration pour les écrans haute résolution
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
    except AttributeError:
        # Ces attributs peuvent ne pas exister dans certaines versions de PyQt6
        pass
    
    # Police par défaut plus moderne
    try:
        # Essayer d'utiliser des polices système modernes
        font_families = ['Segoe UI', 'SF Pro Display', 'Inter', 'Roboto', 'Arial']
        for family in font_families:
            font = QFont(family, 10)
            if QFontDatabase.hasFamily(family):
                app.setFont(font)
                break
    except Exception:
        pass
    
    return app

def main():
    """Point d'entrée principal"""
    try:
        # Créer et configurer l'application
        app = setup_application()
        
        # Créer la fenêtre principale
        window = MainWindow()
        window.show()
        
        # Centrer la fenêtre
        screen = app.primaryScreen()
        screen_geometry = screen.geometry()
        window_geometry = window.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        window.move(x, y)
        
        # Démarrer la boucle d'événements
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"Erreur lors du démarrage de l'application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()