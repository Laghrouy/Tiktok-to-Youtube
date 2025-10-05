"""
Fenêtre principale de l'application TikTok to YouTube
Interface moderne avec direction artistique sombre et dégradés
"""

import sys
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QGridLayout, QLabel, QLineEdit, QTextEdit, QPushButton,
                            QComboBox, QCheckBox, QGroupBox, QTabWidget, QFrame,
                            QScrollArea, QSplitter, QProgressBar, QSpacerItem,
                            QSizePolicy, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QPropertyAnimation, QRect
from PyQt6.QtGui import QFont, QPixmap, QIcon
import threading
import requests
from PIL import Image
from io import BytesIO

# Import des modules existants
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(parent_dir)
from t2y.downloader import download_tiktok_with_info
from t2y.uploader import upload_to_youtube
from googleapiclient.errors import HttpError
from t2y.metadata import fetch_tiktok_metadata
from t2y.validators import is_valid_tiktok_url
from t2y.constants import YOUTUBE_CATEGORIES, LANGUAGES, LICENSES

# Import des styles et composants
from .styles import get_main_stylesheet, DARK_THEME
from .components import (GradientProgressBar, AnimatedButton, StatusCard, 
                        LoadingSpinner, ImagePreview, MetricsCard)

class TikTokProcessor(QThread):
    """Thread pour traiter le téléchargement et l'upload"""
    
    progress_download = pyqtSignal(float)
    progress_upload = pyqtSignal(float)
    status_changed = pyqtSignal(str)
    finished_success = pyqtSignal(str)  # video_id
    finished_error = pyqtSignal(str)   # error_message
    metadata_fetched = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.url = ""
        self.title = ""
        self.description = ""
        self.privacy = "public"
        self.advanced_options = {}
        self.should_cancel = False
        
    def set_data(self, url, title, description, privacy, advanced_options=None):
        self.url = url
        self.title = title
        self.description = description  
        self.privacy = privacy
        self.advanced_options = advanced_options or {}
        
    def cancel(self):
        self.should_cancel = True
        
    def run(self):
        try:
            self.should_cancel = False
            
            # Étape 1: Téléchargement
            self.status_changed.emit("Téléchargement en cours...")
            video_file, info = download_tiktok_with_info(
                self.url,
                on_progress=self._download_progress
            )
            
            if self.should_cancel:
                return
                
            # Étape 2: Upload
            self.status_changed.emit("Upload vers YouTube...")
            video_id = upload_to_youtube(
                video_file, 
                self.title, 
                self.description, 
                self.privacy,
                on_progress=self._upload_progress,
                advanced=self.advanced_options
            )
            
            if self.should_cancel:
                return
                
            self.finished_success.emit(video_id)
            
        except Exception as e:
            if not self.should_cancel:
                self.finished_error.emit(str(e))
    
    def _download_progress(self, pct):
        if not self.should_cancel:
            self.progress_download.emit(pct)
    
    def _upload_progress(self, pct):
        if not self.should_cancel:
            self.progress_upload.emit(pct)

class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.processor = TikTokProcessor()
        self.setup_connections()
        self.init_ui()
        
    def setup_connections(self):
        """Configure les connexions entre signaux et slots"""
        self.processor.progress_download.connect(self.update_download_progress)
        self.processor.progress_upload.connect(self.update_upload_progress)
        self.processor.status_changed.connect(self.update_status)
        self.processor.finished_success.connect(self.on_success)
        self.processor.finished_error.connect(self.on_error)
        self.processor.metadata_fetched.connect(self.on_metadata_fetched)
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("TikTok to YouTube • Modern Edition")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(get_main_stylesheet())
        
        # Widget central avec scroll
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal avec marges
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Frame principal avec effet de verre
        main_frame = QFrame()
        main_frame.setObjectName("main_frame")
        main_layout.addWidget(main_frame)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(25)
        
        # En-tête
        self.create_header(frame_layout)
        
        # Zone de contenu avec splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        frame_layout.addWidget(splitter)
        
        # Panneau gauche - Formulaire
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Panneau droit - Aperçu et statut
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Définir les tailles des panneaux
        splitter.setSizes([700, 500])
        
        # Barre d'état en bas
        self.create_status_bar(frame_layout)
        
    def create_header(self, layout):
        """Crée l'en-tête de l'application"""
        header_layout = QVBoxLayout()
        
        # Titre principal
        title = QLabel("TikTok → YouTube")
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        
        # Sous-titre
        subtitle = QLabel("Convertisseur moderne avec style")
        subtitle.setObjectName("subtitle_label")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)
        
        layout.addLayout(header_layout)
        
    def create_left_panel(self):
        """Crée le panneau gauche avec le formulaire"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        
        # Section URL TikTok
        url_group = self.create_url_section()
        layout.addWidget(url_group)
        
        # Section Informations YouTube
        info_group = self.create_info_section()
        layout.addWidget(info_group)
        
        # Section Options avancées
        advanced_group = self.create_advanced_section()
        layout.addWidget(advanced_group)
        
        # Boutons d'action
        actions_layout = self.create_action_buttons()
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        scroll.setWidget(content)
        return scroll
        
    def create_url_section(self):
        """Crée la section pour l'URL TikTok"""
        group = QGroupBox("🎵 Vidéo TikTok")
        layout = QVBoxLayout(group)
        
        # URL input
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Collez l'URL de la vidéo TikTok ici...")
        self.url_input.textChanged.connect(self.on_url_changed)
        
        self.fetch_metadata_btn = AnimatedButton("📝 Préremplir")
        self.fetch_metadata_btn.setObjectName("secondary_button")
        self.fetch_metadata_btn.clicked.connect(self.fetch_metadata)
        self.fetch_metadata_btn.setEnabled(False)
        
        url_layout.addWidget(self.url_input, 3)
        url_layout.addWidget(self.fetch_metadata_btn, 1)
        
        layout.addLayout(url_layout)
        
        # Indicateur de validité
        self.url_status = QLabel("")
        self.url_status.setObjectName("status_label")
        layout.addWidget(self.url_status)
        
        return group
        
    def create_info_section(self):
        """Crée la section des informations YouTube"""
        group = QGroupBox("📺 Informations YouTube")
        layout = QVBoxLayout(group)
        
        # Titre
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Titre de la vidéo YouTube")
        layout.addWidget(QLabel("Titre :"))
        layout.addWidget(self.title_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description de la vidéo...")
        self.description_input.setMaximumHeight(120)
        layout.addWidget(QLabel("Description :"))
        layout.addWidget(self.description_input)
        
        # Options en ligne
        options_layout = QGridLayout()
        
        # Visibilité
        options_layout.addWidget(QLabel("Visibilité :"), 0, 0)
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems(["public", "unlisted", "private"])
        options_layout.addWidget(self.privacy_combo, 0, 1)
        
        # Catégorie
        options_layout.addWidget(QLabel("Catégorie :"), 1, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItems(list(YOUTUBE_CATEGORIES.keys()))
        self.category_combo.setCurrentText("Entertainment")
        options_layout.addWidget(self.category_combo, 1, 1)
        
        layout.addLayout(options_layout)
        
        return group
        
    def create_advanced_section(self):
        """Crée la section des options avancées"""
        group = QGroupBox("⚙️ Options avancées")
        layout = QVBoxLayout(group)
        
        # Tabs pour organiser les options
        tabs = QTabWidget()
        
        # Tab Général
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Tags
        general_layout.addWidget(QLabel("Tags (séparés par des virgules) :"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tag1, tag2, tag3...")
        general_layout.addWidget(self.tags_input)
        
        # Langue
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Langue :"))
        self.language_combo = QComboBox()
        self.language_combo.addItems(list(LANGUAGES.keys()))
        self.language_combo.setCurrentText("Français (fr)")
        lang_layout.addWidget(self.language_combo)
        general_layout.addLayout(lang_layout)
        
        # Options checkboxes
        self.made_for_kids = QCheckBox("Contenu pour enfants")
        self.auto_shorts = QCheckBox("Conversion automatique en Shorts si < 60s")
        self.auto_shorts.setChecked(True)
        
        general_layout.addWidget(self.made_for_kids)
        general_layout.addWidget(self.auto_shorts)
        general_layout.addStretch()
        
        tabs.addTab(general_tab, "Général")
        
        # Tab Qualité
        quality_tab = QWidget()
        quality_layout = QVBoxLayout(quality_tab)
        
        self.normalize_audio = QCheckBox("Normaliser l'audio")
        self.remux_video = QCheckBox("Optimiser le fichier (remux)")
        self.remux_video.setChecked(True)
        
        quality_layout.addWidget(self.normalize_audio)
        quality_layout.addWidget(self.remux_video)
        quality_layout.addStretch()
        
        tabs.addTab(quality_tab, "Qualité")
        
        layout.addWidget(tabs)
        return group
        
    def create_action_buttons(self):
        """Crée les boutons d'action"""
        layout = QHBoxLayout()
        
        self.start_btn = AnimatedButton("🚀 Lancer le traitement")
        self.start_btn.setObjectName("success_button")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setEnabled(False)
        
        self.cancel_btn = AnimatedButton("⏹️ Annuler")
        self.cancel_btn.setObjectName("danger_button")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        
        layout.addWidget(self.start_btn)
        layout.addWidget(self.cancel_btn)
        
        return layout
        
    def create_right_panel(self):
        """Crée le panneau droit avec aperçu et statut"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aperçu de la vidéo
        preview_group = QGroupBox("👁️ Aperçu")
        preview_layout = QVBoxLayout(preview_group)
        
        self.image_preview = ImagePreview()
        preview_layout.addWidget(self.image_preview)
        
        # Métriques
        metrics_layout = QHBoxLayout()
        self.duration_metric = MetricsCard("Durée", "0", "sec")
        self.size_metric = MetricsCard("Taille", "0", "MB")
        self.resolution_metric = MetricsCard("Résolution", "0x0", "px")
        
        metrics_layout.addWidget(self.duration_metric)
        metrics_layout.addWidget(self.size_metric)
        metrics_layout.addWidget(self.resolution_metric)
        
        preview_layout.addLayout(metrics_layout)
        layout.addWidget(preview_group)
        
        # Progression
        progress_group = QGroupBox("📊 Progression")
        progress_layout = QVBoxLayout(progress_group)
        
        # Téléchargement
        progress_layout.addWidget(QLabel("Téléchargement TikTok :"))
        self.download_progress = GradientProgressBar()
        progress_layout.addWidget(self.download_progress)
        
        # Upload
        progress_layout.addWidget(QLabel("Upload YouTube :"))
        self.upload_progress = GradientProgressBar()
        progress_layout.addWidget(self.upload_progress)
        
        layout.addWidget(progress_group)
        
        # Status cards
        self.status_cards_layout = QVBoxLayout()
        layout.addLayout(self.status_cards_layout)
        
        layout.addStretch()
        return widget
        
    def create_status_bar(self, layout):
        """Crée la barre de statut"""
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("Prêt à traiter une vidéo TikTok")
        self.status_label.setObjectName("status_label")
        
        self.loading_spinner = LoadingSpinner()
        self.loading_spinner.hide()
        
        status_layout.addWidget(self.loading_spinner)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        layout.addLayout(status_layout)
        
    def on_url_changed(self):
        """Gestionnaire de changement d'URL"""
        url = self.url_input.text().strip()
        
        if not url:
            self.url_status.setText("")
            self.fetch_metadata_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            return
            
        if is_valid_tiktok_url(url):
            self.url_status.setText("✅ URL TikTok valide")
            self.url_status.setStyleSheet("color: #10b981;")  # success
            self.fetch_metadata_btn.setEnabled(True)
            self.update_start_button_state()
        else:
            self.url_status.setText("❌ URL TikTok invalide")
            self.url_status.setStyleSheet("color: #ef4444;")  # error
            self.fetch_metadata_btn.setEnabled(False)
            self.start_btn.setEnabled(False)
            
    def update_start_button_state(self):
        """Met à jour l'état du bouton de démarrage"""
        url_valid = is_valid_tiktok_url(self.url_input.text().strip())
        title_valid = bool(self.title_input.text().strip())
        not_processing = not self.processor.isRunning()
        
        self.start_btn.setEnabled(url_valid and title_valid and not_processing)
        
    def fetch_metadata(self):
        """Récupère les métadonnées de la vidéo TikTok"""
        url = self.url_input.text().strip()
        if not is_valid_tiktok_url(url):
            return
            
        self.add_status_card("Récupération des métadonnées...", "info")
        self.loading_spinner.start()
        
        # Utiliser un thread pour éviter de bloquer l'UI
        def fetch_worker():
            try:
                metadata = fetch_tiktok_metadata(url)
                # Émettre via le processor (QObject) pour un dispatch thread-safe
                self.processor.metadata_fetched.emit(metadata)
            except Exception as e:
                self.processor.finished_error.emit(f"Erreur lors de la récupération des métadonnées: {str(e)}")
        
        thread = threading.Thread(target=fetch_worker)
        thread.daemon = True
        thread.start()
        
    def on_metadata_fetched(self, metadata):
        """Gestionnaire de réception des métadonnées"""
        self.loading_spinner.stop()
        
        if metadata:
            # Préremplir les champs
            if metadata.get('title'):
                self.title_input.setText(metadata['title'])
                
            if metadata.get('description'):
                self.description_input.setPlainText(metadata['description'])
                
            if metadata.get('hashtags'):
                tags = ', '.join(metadata['hashtags'])
                self.tags_input.setText(tags)
                
            # Charger la miniature
            if metadata.get('thumbnail'):
                self.load_thumbnail(metadata['thumbnail'])
                
            # Mettre à jour les métriques
            if metadata.get('duration'):
                self.duration_metric.update_value(int(metadata['duration']), "sec")
                
            if metadata.get('width') and metadata.get('height'):
                resolution = f"{metadata['width']}x{metadata['height']}"
                self.resolution_metric.update_value(resolution, "")
                
            self.add_status_card("Métadonnées récupérées avec succès", "success")
        else:
            self.add_status_card("Impossible de récupérer les métadonnées", "warning")
            
        self.update_start_button_state()
        
    def load_thumbnail(self, url):
        """Charge la miniature de la vidéo"""
        def load_worker():
            try:
                response = requests.get(url, timeout=10)
                image = Image.open(BytesIO(response.content))
                
                # Redimensionner
                image.thumbnail((300, 200), Image.Resampling.LANCZOS)
                
                # Convertir en QPixmap
                qimage = image.convert('RGB')
                width, height = qimage.size
                bytes_per_line = 3 * width
                
                from PyQt6.QtGui import QImage
                q_image = QImage(qimage.tobytes(), width, height, bytes_per_line, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(q_image)
                
                # Mettre à jour l'UI dans le thread principal
                self.image_preview.setPixmap(pixmap)
                self.image_preview.setScaledContents(True)
                
            except Exception as e:
                print(f"Erreur lors du chargement de la miniature: {e}")
                
        thread = threading.Thread(target=load_worker)
        thread.daemon = True  
        thread.start()
        
    def start_processing(self):
        """Démarre le traitement de la vidéo"""
        url = self.url_input.text().strip()
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        privacy = self.privacy_combo.currentText()
        
        # Options avancées
        advanced_options = {
            'tags': [tag.strip() for tag in self.tags_input.text().split(',') if tag.strip()],
            'categoryId': YOUTUBE_CATEGORIES.get(self.category_combo.currentText(), '24'),
            'defaultLanguage': LANGUAGES.get(self.language_combo.currentText()),
            'madeForKids': self.made_for_kids.isChecked(),
            'ff_normalize': self.normalize_audio.isChecked(),
            'ff_remux': self.remux_video.isChecked(),
        }
        
        # Reset des barres de progression
        self.download_progress.setValue(0)
        self.upload_progress.setValue(0)
        
        # Clear previous status cards
        self.clear_status_cards()
        
        # Configurer et démarrer le processor
        self.processor.set_data(url, title, description, privacy, advanced_options)
        self.processor.start()
        
        # Mettre à jour l'UI
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.loading_spinner.start()
        
        self.add_status_card("Traitement démarré", "info")
        
    def cancel_processing(self):
        """Annule le traitement en cours"""
        self.processor.cancel()
        self.loading_spinner.stop()
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.add_status_card("Traitement annulé", "warning")
        
    def update_download_progress(self, value):
        """Met à jour la progression du téléchargement"""
        self.download_progress.setValue(int(value))
        
    def update_upload_progress(self, value):
        """Met à jour la progression de l'upload"""
        self.upload_progress.setValue(int(value))
        
    def update_status(self, message):
        """Met à jour le message de statut"""
        self.status_label.setText(message)
        
    def on_success(self, video_id):
        """Gestionnaire de succès"""
        self.loading_spinner.stop()
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.update_start_button_state()
        
        success_message = f"Vidéo uploadée avec succès!\\nID: {video_id}"
        self.add_status_card(success_message, "success")
        
        # Proposer d'ouvrir la vidéo
        reply = QMessageBox.question(self, "Succès", 
                                   f"Vidéo uploadée avec succès!\\n\\nID: {video_id}\\n\\nVoulez-vous ouvrir la vidéo sur YouTube?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            import webbrowser
            webbrowser.open(f"https://youtu.be/{video_id}")
            
    def on_error(self, error_message):
        """Gestionnaire d'erreur"""
        self.loading_spinner.stop()
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.update_start_button_state()
        
        # Guidance spéciale pour 401 non authentifié
        guidance = ""
        if "401" in error_message or "Login Required" in error_message or "authentication" in error_message.lower():
            guidance = "\n\nAstuce: Cliquez sur 'Préremplir' ou relancez l'upload; une fenêtre de connexion Google peut s'ouvrir pour autoriser l'application. Assurez-vous que client_secret.json est valide."
        self.add_status_card(f"Erreur: {error_message}{guidance}", "error")
        
        QMessageBox.critical(self, "Erreur", f"Une erreur s'est produite:\\n\\n{error_message}")
        
    def add_status_card(self, message, card_type="info"):
        """Ajoute une carte de statut"""
        card = StatusCard("", message, card_type)
        self.status_cards_layout.addWidget(card)
        
        # Limiter le nombre de cartes affichées
        if self.status_cards_layout.count() > 5:
            old_card = self.status_cards_layout.takeAt(0)
            if old_card and old_card.widget():
                old_card.widget().deleteLater()
                
    def clear_status_cards(self):
        """Efface toutes les cartes de statut"""
        while self.status_cards_layout.count():
            child = self.status_cards_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def closeEvent(self, event):
        """Gestionnaire de fermeture de l'application"""
        if self.processor.isRunning():
            reply = QMessageBox.question(self, "Fermeture", 
                                       "Un traitement est en cours. Voulez-vous vraiment quitter?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                self.processor.cancel()
                self.processor.wait(3000)  # Attendre 3 secondes max
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()