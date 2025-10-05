"""
Version de démonstration simplifiée pour tester l'interface
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton,
                            QTextEdit, QComboBox, QGroupBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class SimpleMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("TikTok → YouTube • Modern Edition")
        self.setMinimumSize(1000, 700)
        
        # Style sombre moderne
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:1 #1a1a2e);
                color: #ffffff;
            }
            
            QWidget {
                background: transparent;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.08),
                    stop:1 rgba(255, 255, 255, 0.03));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                margin: 10px;
                padding-top: 20px;
                font-weight: 600;
                font-size: 16px;
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 5px 15px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #06b6d4);
                border-radius: 8px;
                color: white;
                font-weight: bold;
            }
            
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: #ffffff;
                min-height: 20px;
            }
            
            QLineEdit:focus {
                border: 2px solid #8b5cf6;
                background: rgba(139, 92, 246, 0.1);
            }
            
            QTextEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                color: #ffffff;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                border: none;
                border-radius: 12px;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 24px;
                min-height: 20px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #8b5cf6);
            }
            
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6d28d9, stop:1 #5b21b6);
            }
            
            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: #ffffff;
                min-height: 20px;
            }
            
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 24px;
            }
            
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:0.5 #06b6d4, stop:1 #ec4899);
                border-radius: 6px;
                margin: 1px;
            }
        """)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Titre
        title = QLabel("TikTok → YouTube")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: #ffffff;
            margin: 20px 0;
        """)
        main_layout.addWidget(title)
        
        # Section URL
        url_group = QGroupBox("🎵 Vidéo TikTok")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Collez l'URL de la vidéo TikTok ici...")
        url_layout.addWidget(self.url_input)
        
        main_layout.addWidget(url_group)
        
        # Section YouTube
        yt_group = QGroupBox("📺 Informations YouTube")
        yt_layout = QVBoxLayout(yt_group)
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titre de la vidéo YouTube")
        yt_layout.addWidget(QLabel("Titre :"))
        yt_layout.addWidget(self.title_input)
        
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description de la vidéo...")
        self.description_input.setMaximumHeight(100)
        yt_layout.addWidget(QLabel("Description :"))
        yt_layout.addWidget(self.description_input)
        
        # Options
        options_layout = QHBoxLayout()
        options_layout.addWidget(QLabel("Visibilité :"))
        
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems(["public", "unlisted", "private"])
        options_layout.addWidget(self.privacy_combo)
        
        yt_layout.addLayout(options_layout)
        main_layout.addWidget(yt_group)
        
        # Progression
        progress_group = QGroupBox("📊 Progression")
        progress_layout = QVBoxLayout(progress_group)
        
        progress_layout.addWidget(QLabel("Téléchargement :"))
        self.download_progress = QProgressBar()
        self.download_progress.setValue(0)
        progress_layout.addWidget(self.download_progress)
        
        progress_layout.addWidget(QLabel("Upload :"))
        self.upload_progress = QProgressBar()
        self.upload_progress.setValue(0)
        progress_layout.addWidget(self.upload_progress)
        
        main_layout.addWidget(progress_group)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Lancer le traitement")
        self.cancel_btn = QPushButton("⏹️ Annuler")
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Status
        self.status_label = QLabel("Prêt à traiter une vidéo TikTok")
        self.status_label.setStyleSheet("""
            color: #a1a1aa;
            font-size: 14px;
            padding: 8px 12px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        main_layout.addWidget(self.status_label)
        
        # Test des barres de progression
        self.test_progress()
        
    def test_progress(self):
        """Test animé des barres de progression"""
        from PyQt6.QtCore import QTimer
        
        self.timer = QTimer()
        self.progress_value = 0
        
        def update_progress():
            self.progress_value += 2
            if self.progress_value <= 100:
                self.download_progress.setValue(self.progress_value)
                if self.progress_value > 50:
                    self.upload_progress.setValue(self.progress_value - 50)
            else:
                self.timer.stop()
                self.status_label.setText("✅ Traitement terminé avec succès!")
        
        self.timer.timeout.connect(update_progress)
        self.timer.start(100)  # Mise à jour toutes les 100ms

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TikTok to YouTube Demo")
    
    window = SimpleMainWindow()
    window.show()
    
    # Centrer la fenêtre
    screen = app.primaryScreen()
    screen_geometry = screen.geometry()
    window_geometry = window.geometry()
    x = (screen_geometry.width() - window_geometry.width()) // 2
    y = (screen_geometry.height() - window_geometry.height()) // 2
    window.move(x, y)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()