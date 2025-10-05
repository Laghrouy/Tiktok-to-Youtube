#!/usr/bin/env python3
"""
Application desktop TikTok to YouTube - Version finale optimisée
Application moderne avec interface PyQt6 et styles optimisés
"""

import sys
import os
from pathlib import Path

# Configuration du path pour importer les modules
SCRIPT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
        QLabel, QLineEdit, QTextEdit, QPushButton, QProgressBar,
        QGroupBox, QGridLayout, QSpacerItem, QSizePolicy, QFrame,
        QComboBox, QCheckBox, QFileDialog, QMessageBox, QTabWidget
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QRect
    from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
except ImportError as e:
    print(f"Erreur d'import PyQt6: {e}")
    print("Installez PyQt6 avec: pip install PyQt6")
    sys.exit(1)

# Import du stylesheet optimisé
try:
    from ui.styles_optimized import get_optimized_stylesheet, DARK_THEME
except ImportError:
    print("Utilisation du style par défaut")
    def get_optimized_stylesheet():
        return ""
    DARK_THEME = {}

# Import des modules business via adaptateurs
try:
    from adapters import TikTokDownloader, YouTubeUploader, MetadataProcessor
    from t2y.logger import log as setup_logger
    BUSINESS_MODULES_AVAILABLE = True
    print("✅ Modules t2y chargés avec succès via adaptateurs")
except ImportError as e:
    print(f"⚠️  Modules t2y non trouvés: {e}")
    print("🎪 Mode démo activé - fonctionnalités simulées")
    BUSINESS_MODULES_AVAILABLE = False
    # Mode démo sans modules business
    class MockClass:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return self
        def __getattr__(self, name): return MockClass()
    
    TikTokDownloader = YouTubeUploader = MetadataProcessor = MockClass
    setup_logger = lambda *args: MockClass()

# Configuration simple
class Config:
    """Configuration simple pour l'application"""
    def __init__(self):
        self.settings = {
            'quality': '1080p',
            'format': 'mp4',
            'privacy': 'public',
            'category': 'Entertainment'
        }

class ProcessingThread(QThread):
    """Thread pour traitement en arrière-plan"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, url, config):
        super().__init__()
        self.url = url
        self.config = config
        self.logger = setup_logger()
        
    def run(self):
        try:
            if not BUSINESS_MODULES_AVAILABLE:
                # Mode simulation pour démo
                self.status_updated.emit("🎪 Mode démo - Simulation du téléchargement...")
                self.progress_updated.emit(20)
                self.msleep(1000)
                
                self.status_updated.emit("📱 Simulation: Vidéo TikTok téléchargée")
                self.progress_updated.emit(40)
                self.msleep(1000)
                
                self.status_updated.emit("� Simulation: Métadonnées préparées")
                self.progress_updated.emit(60)
                self.msleep(1000)
                
                self.status_updated.emit("🎉 Simulation: Upload terminé!")
                self.progress_updated.emit(100)
                self.finished.emit(True, "demo_video_id_12345")
                return
            
            self.status_updated.emit("�🔍 Analyse de l'URL TikTok...")
            self.progress_updated.emit(20)
            
            # Téléchargement TikTok
            downloader = TikTokDownloader()
            video_path = downloader.download(self.url, on_progress=lambda p: self.progress_updated.emit(20 + p * 0.2))
            
            if not video_path:
                self.finished.emit(False, "Erreur lors du téléchargement")
                return
                
            self.status_updated.emit("📱 Vidéo TikTok téléchargée")
            self.progress_updated.emit(40)
            
            # Traitement des métadonnées
            metadata_processor = MetadataProcessor()
            config_with_url = dict(self.config)
            config_with_url['source_url'] = self.url
            config_with_url['on_progress'] = lambda p: self.progress_updated.emit(60 + p * 0.4)
            metadata = metadata_processor.process(video_path, config_with_url)
            
            self.status_updated.emit("📝 Métadonnées préparées")
            self.progress_updated.emit(60)
            
            # Upload vers YouTube
            uploader = YouTubeUploader()
            upload_result = uploader.upload(video_path, metadata)
            
            if upload_result:
                self.status_updated.emit("🎉 Upload terminé avec succès!")
                self.progress_updated.emit(100)
                self.finished.emit(True, f"Vidéo uploadée: {upload_result}")
            else:
                self.finished.emit(False, "Erreur lors de l'upload")
                
        except Exception as e:
            self.logger.error(f"Erreur de traitement: {e}")
            self.finished.emit(False, str(e))

class TikTokToYouTubeApp(QMainWindow):
    """Application principale TikTok to YouTube"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.processing_thread = None
        
        # Configuration de la fenêtre
        self.setWindowTitle("TikTok to YouTube - Converter Pro")
        self.setMinimumSize(900, 700)
        self.resize(1200, 800)
        
        # Application du style optimisé
        self.setStyleSheet(get_optimized_stylesheet())
        
        # Interface utilisateur
        self.setup_ui()
        
        # Centrage de la fenêtre
        self.center_on_screen()
        
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Frame principal avec style glassmorphism
        main_frame = QFrame()
        main_frame.setObjectName("main_frame")
        main_layout.addWidget(main_frame)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(20)
        
        # En-tête avec titre
        self.create_header(frame_layout)
        
        # Contenu principal avec onglets
        self.create_tabs(frame_layout)
        
        # Barre de progression et statut
        self.create_progress_section(frame_layout)
        
    def create_header(self, layout):
        """Création de l'en-tête"""
        header_layout = QVBoxLayout()
        
        # Titre principal
        title = QLabel("TikTok to YouTube Converter")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Sous-titre
        subtitle = QLabel("Transformez vos vidéos TikTok en contenu YouTube professionnel")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
    def create_tabs(self, layout):
        """Création des onglets principaux"""
        self.tabs = QTabWidget()
        
        # Onglet Principal
        main_tab = self.create_main_tab()
        self.tabs.addTab(main_tab, "🎬 Conversion")
        
        # Onglet Configuration
        config_tab = self.create_config_tab()
        self.tabs.addTab(config_tab, "⚙️ Configuration")
        
        # Onglet Historique
        history_tab = self.create_history_tab()
        self.tabs.addTab(history_tab, "📋 Historique")
        
        layout.addWidget(self.tabs)
        
    def create_main_tab(self):
        """Onglet principal de conversion"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Section URL TikTok
        url_group = QGroupBox("📱 URL TikTok")
        url_layout = QVBoxLayout(url_group)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.tiktok.com/@username/video/...")
        url_layout.addWidget(self.url_input)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("👁️ Prévisualiser")
        self.preview_btn.setObjectName("secondary_button")
        self.preview_btn.clicked.connect(self.preview_video)
        
        self.convert_btn = QPushButton("🚀 Convertir et Uploader")
        self.convert_btn.clicked.connect(self.start_conversion)
        
        button_layout.addWidget(self.preview_btn)
        button_layout.addWidget(self.convert_btn)
        url_layout.addLayout(button_layout)
        
        layout.addWidget(url_group)
        
        # Section Métadonnées YouTube
        metadata_group = QGroupBox("📝 Métadonnées YouTube")
        metadata_layout = QGridLayout(metadata_group)
        
        metadata_layout.addWidget(QLabel("Titre:"), 0, 0)
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titre de la vidéo YouTube")
        metadata_layout.addWidget(self.title_input, 0, 1)
        
        metadata_layout.addWidget(QLabel("Description:"), 1, 0)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description détaillée...")
        self.description_input.setMaximumHeight(100)
        metadata_layout.addWidget(self.description_input, 1, 1)
        
        metadata_layout.addWidget(QLabel("Tags:"), 2, 0)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3...")
        metadata_layout.addWidget(self.tags_input, 2, 1)
        
        metadata_layout.addWidget(QLabel("Catégorie:"), 3, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Divertissement", "Éducation", "Musique", "Gaming",
            "Science & Technologie", "Sport", "Voyage", "Mode"
        ])
        metadata_layout.addWidget(self.category_combo, 3, 1)
        
        layout.addWidget(metadata_group)
        
        # Options avancées
        options_group = QGroupBox("🔧 Options avancées")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_metadata_cb = QCheckBox("Générer automatiquement les métadonnées")
        self.auto_metadata_cb.setChecked(True)
        options_layout.addWidget(self.auto_metadata_cb)
        
        self.enhance_quality_cb = QCheckBox("Améliorer la qualité vidéo")
        options_layout.addWidget(self.enhance_quality_cb)
        
        self.add_watermark_cb = QCheckBox("Ajouter un watermark")
        options_layout.addWidget(self.add_watermark_cb)
        
        layout.addWidget(options_group)
        
        # Spacer
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return tab
        
    def create_config_tab(self):
        """Onglet de configuration"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Configuration YouTube
        youtube_group = QGroupBox("🔑 Configuration YouTube")
        youtube_layout = QGridLayout(youtube_group)
        
        youtube_layout.addWidget(QLabel("Client ID:"), 0, 0)
        self.client_id_input = QLineEdit()
        self.client_id_input.setEchoMode(QLineEdit.EchoMode.Password)
        youtube_layout.addWidget(self.client_id_input, 0, 1)
        
        auth_btn = QPushButton("🔐 Authentifier YouTube")
        auth_btn.setObjectName("secondary_button")
        youtube_layout.addWidget(auth_btn, 1, 0, 1, 2)
        
        layout.addWidget(youtube_group)
        
        # Configuration avancée
        advanced_group = QGroupBox("⚙️ Paramètres avancés")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Qualité par défaut
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Qualité par défaut:"))
        quality_combo = QComboBox()
        quality_combo.addItems(["1080p", "720p", "480p", "Auto"])
        quality_layout.addWidget(quality_combo)
        advanced_layout.addLayout(quality_layout)
        
        # Dossier de téléchargement
        download_layout = QHBoxLayout()
        download_layout.addWidget(QLabel("Dossier de téléchargement:"))
        download_path = QLineEdit()
        download_path.setText(str(Path.home() / "Downloads"))
        download_btn = QPushButton("📁 Parcourir")
        download_btn.clicked.connect(lambda: self.select_download_folder(download_path))
        download_layout.addWidget(download_path)
        download_layout.addWidget(download_btn)
        advanced_layout.addLayout(download_layout)
        
        layout.addWidget(advanced_group)
        
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return tab
        
    def create_history_tab(self):
        """Onglet historique"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        history_group = QGroupBox("📋 Historique des conversions")
        history_layout = QVBoxLayout(history_group)
        
        # Liste des conversions (placeholder)
        history_label = QLabel("Aucune conversion effectuée pour le moment.")
        history_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        history_label.setObjectName("status_label")
        history_layout.addWidget(history_label)
        
        layout.addWidget(history_group)
        
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        return tab
        
    def create_progress_section(self, layout):
        """Section de progression"""
        progress_group = QGroupBox("📊 Progression")
        progress_layout = QVBoxLayout(progress_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Label de statut
        self.status_label = QLabel("Prêt à convertir...")
        self.status_label.setObjectName("status_label")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        layout.addWidget(progress_group)
        
    def preview_video(self):
        """Prévisualisation de la vidéo TikTok"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une URL TikTok")
            return
            
        self.status_label.setText("🔍 Chargement de la prévisualisation...")
        # Logique de prévisualisation ici
        
    def start_conversion(self):
        """Démarrage du processus de conversion"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer une URL TikTok")
            return
            
        # Configuration
        config = {
            'title': self.title_input.text() or None,
            'description': self.description_input.toPlainText() or None,
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()],
            'category': self.category_combo.currentText(),
            'auto_metadata': self.auto_metadata_cb.isChecked(),
            'enhance_quality': self.enhance_quality_cb.isChecked(),
            'add_watermark': self.add_watermark_cb.isChecked()
        }
        
        # Démarrage du thread de traitement
        self.processing_thread = ProcessingThread(url, config)
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.status_updated.connect(self.update_status)
        self.processing_thread.finished.connect(self.conversion_finished)
        
        # Interface
        self.convert_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.processing_thread.start()
        
    def update_progress(self, value):
        """Mise à jour de la barre de progression"""
        self.progress_bar.setValue(value)
        
    def update_status(self, message):
        """Mise à jour du statut"""
        self.status_label.setText(message)
        
    def conversion_finished(self, success, message):
        """Fin de la conversion"""
        self.convert_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ Conversion terminée avec succès!")
            QMessageBox.information(self, "Succès", message)
        else:
            self.status_label.setText("❌ Erreur lors de la conversion")
            QMessageBox.critical(self, "Erreur", message)
            
    def select_download_folder(self, path_input):
        """Sélection du dossier de téléchargement"""
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier")
        if folder:
            path_input.setText(folder)
            
    def center_on_screen(self):
        """Centre la fenêtre sur l'écran"""
        screen = QApplication.primaryScreen().geometry()
        window = self.frameGeometry()
        window.moveCenter(screen.center())
        self.move(window.topLeft())

def main():
    """Fonction principale"""
    app = QApplication(sys.argv)
    
    # Configuration de l'application
    app.setApplicationName("TikTok to YouTube Converter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("T2Y Studio")
    
    # Style sombre par défaut
    app.setStyle("Fusion")
    
    # Création et affichage de la fenêtre
    window = TikTokToYouTubeApp()
    window.show()
    
    # Boucle d'événements
    sys.exit(app.exec())

if __name__ == "__main__":
    main()