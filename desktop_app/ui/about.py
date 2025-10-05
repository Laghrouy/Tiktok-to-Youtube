"""
Fenêtre À propos de l'application
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QLinearGradient, QColor

class AboutDialog(QDialog):
    """Fenêtre À propos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos de TikTok to YouTube Desktop")
        self.setModal(True)
        self.setFixedSize(500, 600)
        self.init_ui()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Logo/Titre stylisé
        self.create_header(layout)
        
        # Informations de l'application
        self.create_app_info(layout)
        
        # Fonctionnalités
        self.create_features(layout)
        
        # Crédits
        self.create_credits(layout)
        
        # Bouton Fermer
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        close_btn.setObjectName("primary_button")
        
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Style de la fenêtre
        self.setStyleSheet("""
            QDialog {
                background-color: #000000;
                color: #ffffff;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            #title_label {
                font-size: 28px;
                font-weight: bold;
                color: #8b5cf6;
            }
            
            #subtitle_label {
                font-size: 16px;
                color: #a1a1aa;
                font-weight: 500;
            }
            
            #version_label {
                font-size: 14px;
                color: #71717a;
                background: rgba(255, 255, 255, 0.05);
                padding: 4px 12px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            
            #section_title {
                font-size: 18px;
                font-weight: bold;
                color: #8b5cf6;
                margin: 10px 0 5px 0;
            }
            
            #feature_item {
                color: #e5e7eb;
                font-size: 14px;
                margin: 2px 0;
            }
            
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: #a1a1aa;
                font-size: 12px;
                padding: 8px;
            }
            
            QFrame#separator {
                background: rgba(255, 255, 255, 0.1);
                max-height: 1px;
                margin: 10px 0;
            }
            
            QPushButton#primary_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 24px;
                min-width: 100px;
            }
            
            QPushButton#primary_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #8b5cf6);
            }
        """)
        
    def create_header(self, layout):
        """Crée l'en-tête avec logo et titre"""
        header_layout = QVBoxLayout()
        
        # Titre principal
        title = QLabel("TikTok to YouTube")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Sous-titre
        subtitle = QLabel("Desktop • Modern Edition")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        # Version
        version = QLabel("Version 2.0.0")
        version.setObjectName("version_label")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(version)
        
        layout.addLayout(header_layout)
        
        # Séparateur
        separator = QFrame()
        separator.setObjectName("separator")
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(separator)
        
    def create_app_info(self, layout):
        """Crée la section d'informations de l'application"""
        info_layout = QVBoxLayout()
        
        title = QLabel("Description")
        title.setObjectName("section_title")
        info_layout.addWidget(title)
        
        description = QLabel(
            "Application de bureau moderne pour convertir vos vidéos TikTok "
            "en uploads YouTube automatisés. Interface élégante avec direction "
            "artistique sombre et dégradés, animations fluides et composants "
            "personnalisés pour une expérience utilisateur optimale."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #e5e7eb; font-size: 14px; line-height: 1.5;")
        info_layout.addWidget(description)
        
        layout.addLayout(info_layout)
        
    def create_features(self, layout):
        """Crée la section des fonctionnalités"""
        features_layout = QVBoxLayout()
        
        title = QLabel("Fonctionnalités principales")
        title.setObjectName("section_title")
        features_layout.addWidget(title)
        
        features = [
            "🎨 Interface moderne avec design glassmorphism",
            "🚀 Téléchargement TikTok avec aperçu en temps réel", 
            "📺 Upload YouTube automatisé avec toutes les options",
            "🤖 Préremplissage intelligent des métadonnées",
            "🔄 Détection automatique des Shorts (< 60s)",
            "⚙️ Options avancées : tags, catégories, langues",
            "📊 Barres de progression animées et effets visuels",
            "🎯 Gestion des files d'attente et traitement en lot",
            "💾 Configuration personnalisable et thèmes",
            "🔧 Composants UI personnalisés et animations"
        ]
        
        for feature in features:
            label = QLabel(feature)
            label.setObjectName("feature_item")
            features_layout.addWidget(label)
            
        layout.addLayout(features_layout)
        
    def create_credits(self, layout):
        """Crée la section des crédits"""
        credits_layout = QVBoxLayout()
        
        title = QLabel("Technologies utilisées")
        title.setObjectName("section_title")
        credits_layout.addWidget(title)
        
        credits_text = QTextEdit()
        credits_text.setReadOnly(True)
        credits_text.setMaximumHeight(120)
        credits_text.setPlainText(
            "• PyQt6 - Framework d'interface utilisateur moderne\\n"
            "• Python 3.9+ - Langage de programmation\\n"
            "• yt-dlp - Téléchargement de vidéos TikTok\\n"
            "• Google APIs - Integration YouTube\\n"
            "• Pillow - Traitement d'images\\n"
            "• CSS3 - Styles et animations avancés\\n\\n"
            "Développé avec ❤️ par la communauté open source\\n"
            "Basé sur le projet TikTok-to-Youtube de Yacinelgh"
        )
        credits_layout.addWidget(credits_text)
        
        layout.addLayout(credits_layout)
        
        # Copyright
        copyright_label = QLabel("© 2024 TikTok to YouTube Desktop - Open Source")
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setStyleSheet("color: #71717a; font-size: 12px; margin-top: 10px;")
        layout.addWidget(copyright_label)