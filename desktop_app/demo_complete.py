"""
Démonstration complète de l'interface avec toutes les fonctionnalités
Version simplifiée sans dépendances externes complexes
"""

import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QGridLayout, QLabel, QLineEdit, QPushButton,
                            QTextEdit, QComboBox, QCheckBox, QGroupBox, QTabWidget,
                            QProgressBar, QFrame, QScrollArea, QSplitter, QMenuBar,
                            QMenu, QMessageBox, QFileDialog)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QFont, QAction, QPainter, QColor, QLinearGradient

class AnimatedProgressBar(QProgressBar):
    """Barre de progression avec dégradé animé"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setRange(0, 100)
        self.setValue(0)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond
        painter.setBrush(QColor(255, 255, 255, 13))
        painter.drawRoundedRect(self.rect(), 8, 8)
        
        # Barre de progression avec dégradé
        if self.value() > 0:
            progress_width = int((self.value() / self.maximum()) * self.width())
            gradient = QLinearGradient(0, 0, progress_width, 0)
            gradient.setColorAt(0, QColor(139, 92, 246))  # violet
            gradient.setColorAt(0.5, QColor(6, 182, 212))  # cyan
            gradient.setColorAt(1, QColor(236, 72, 153))  # rose
            
            painter.setBrush(gradient)
            painter.drawRoundedRect(1, 1, progress_width - 2, self.height() - 2, 6, 6)
        
        # Texte
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self.value()}%")

class StatusCard(QFrame):
    """Carte de statut avec style"""
    
    def __init__(self, message="", card_type="info", parent=None):
        super().__init__(parent)
        self.init_ui(message, card_type)
        
    def init_ui(self, message, card_type):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        
        label = QLabel(message)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Style selon le type
        colors = {
            'info': '#8b5cf6',
            'success': '#10b981', 
            'warning': '#f59e0b',
            'error': '#ef4444'
        }
        
        color = colors.get(card_type, colors['info'])
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-left: 4px solid {color};
                border-radius: 8px;
                margin: 4px 0;
            }}
            QLabel {{
                color: #ffffff;
                font-size: 14px;
            }}
        """)

class FullDemoWindow(QMainWindow):
    """Fenêtre de démonstration complète"""
    
    def __init__(self):
        super().__init__()
        self.status_cards = []
        self.init_ui()
        self.setup_demo_data()
        
    def init_ui(self):
        self.setWindowTitle("TikTok → YouTube Desktop • Démonstration Complète")
        self.setMinimumSize(1400, 900)
        
        # Style général
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
            
            /* Menu Bar */
            QMenuBar {
                background: rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                padding: 4px;
            }
            
            QMenuBar::item {
                background: transparent;
                padding: 8px 16px;
                border-radius: 6px;
            }
            
            QMenuBar::item:selected {
                background: rgba(139, 92, 246, 0.3);
            }
            
            QMenu {
                background: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
            }
            
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            
            QMenu::item:selected {
                background: #8b5cf6;
            }
            
            /* GroupBox */
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
            
            /* Inputs */
            QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
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
            }
            
            QComboBox {
                background: rgba(255, 255, 255, 0.05);
                border: 2px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                min-height: 20px;
            }
            
            /* Buttons */
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
            
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: #71717a;
            }
            
            QPushButton#secondary_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #06b6d4, stop:1 #0891b2);
            }
            
            QPushButton#danger_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef4444, stop:1 #dc2626);
            }
            
            QPushButton#success_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #10b981, stop:1 #059669);
            }
            
            /* CheckBox */
            QCheckBox {
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.05);
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                border: 2px solid #8b5cf6;
            }
            
            /* Tabs */
            QTabWidget::pane {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.03);
            }
            
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.05);
                color: #a1a1aa;
                padding: 12px 20px;
                margin: 0 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #06b6d4);
                color: white;
            }
            
            /* Progress Bar */
            QProgressBar {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
                height: 28px;
            }
            
            /* ScrollArea */
            QScrollArea {
                border: none;
                background: transparent;
            }
            
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.05);
                width: 12px;
                border-radius: 6px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Menu bar
        self.create_menu_bar()
        
        # Widget central avec layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Titre principal
        title = QLabel("TikTok → YouTube Desktop")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #ffffff;
            margin: 20px 0;
        """)
        main_layout.addWidget(title)
        
        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Panneau gauche - Formulaire
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Panneau droit - Aperçu et status
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([800, 600])
        
    def create_menu_bar(self):
        """Crée la barre de menu"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu('Fichier')
        
        open_action = QAction('Ouvrir URL...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_url_dialog)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        quit_action = QAction('Quitter', self)
        quit_action.setShortcut('Ctrl+Q')
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)
        
        # Menu Outils
        tools_menu = menubar.addMenu('Outils')
        
        prefs_action = QAction('Préférences...', self)
        prefs_action.setShortcut('Ctrl+,')
        prefs_action.triggered.connect(self.show_preferences)
        tools_menu.addAction(prefs_action)
        
        # Menu Aide
        help_menu = menubar.addMenu('Aide')
        
        about_action = QAction('À propos...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_left_panel(self):
        """Crée le panneau gauche avec formulaire"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(20)
        
        # Section URL TikTok
        url_group = QGroupBox("🎵 Vidéo TikTok")
        url_layout = QVBoxLayout(url_group)
        
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.tiktok.com/@user/video/...")
        
        fetch_btn = QPushButton("📝 Préremplir")
        fetch_btn.setObjectName("secondary_button")
        fetch_btn.clicked.connect(self.demo_fetch_metadata)
        
        url_input_layout.addWidget(self.url_input, 3)
        url_input_layout.addWidget(fetch_btn, 1)
        url_layout.addLayout(url_input_layout)
        
        self.url_status = QLabel("")
        url_layout.addWidget(self.url_status)
        
        layout.addWidget(url_group)
        
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
        
        # Options inline
        options_layout = QGridLayout()
        
        options_layout.addWidget(QLabel("Visibilité :"), 0, 0)
        self.privacy_combo = QComboBox()
        self.privacy_combo.addItems(["public", "unlisted", "private"])
        options_layout.addWidget(self.privacy_combo, 0, 1)
        
        options_layout.addWidget(QLabel("Catégorie :"), 1, 0)
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Entertainment", "Music", "Gaming", "Education"])
        options_layout.addWidget(self.category_combo, 1, 1)
        
        yt_layout.addLayout(options_layout)
        layout.addWidget(yt_group)
        
        # Section Options Avancées avec Tabs
        advanced_group = QGroupBox("⚙️ Options avancées")
        advanced_layout = QVBoxLayout(advanced_group)
        
        tabs = QTabWidget()
        
        # Tab Général
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        general_layout.addWidget(QLabel("Tags (séparés par virgules) :"))
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("tiktok, viral, trending...")
        general_layout.addWidget(self.tags_input)
        
        self.auto_shorts_check = QCheckBox("Conversion automatique en Shorts si < 60s")
        self.auto_shorts_check.setChecked(True)
        general_layout.addWidget(self.auto_shorts_check)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "Général")
        
        # Tab Qualité
        quality_tab = QWidget()
        quality_layout = QVBoxLayout(quality_tab)
        
        self.normalize_audio_check = QCheckBox("Normaliser l'audio")
        self.remux_check = QCheckBox("Optimiser le fichier (remux)")
        self.remux_check.setChecked(True)
        
        quality_layout.addWidget(self.normalize_audio_check)
        quality_layout.addWidget(self.remux_check)
        quality_layout.addStretch()
        
        tabs.addTab(quality_tab, "Qualité")
        
        advanced_layout.addWidget(tabs)
        layout.addWidget(advanced_group)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("🚀 Lancer le traitement")
        self.start_btn.setObjectName("success_button")
        self.start_btn.clicked.connect(self.demo_start_processing)
        
        self.cancel_btn = QPushButton("⏹️ Annuler")
        self.cancel_btn.setObjectName("danger_button")
        self.cancel_btn.clicked.connect(self.demo_cancel_processing)
        self.cancel_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        scroll.setWidget(content)
        return scroll
        
    def create_right_panel(self):
        """Crée le panneau droit"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aperçu
        preview_group = QGroupBox("👁️ Aperçu")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_label = QLabel("Aperçu de la vidéo TikTok\\nSera affiché ici après préremplissage")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(255, 255, 255, 0.05),
                stop:1 rgba(255, 255, 255, 0.02));
            border: 2px dashed rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            color: #71717a;
            font-size: 14px;
            min-height: 150px;
        """)
        preview_layout.addWidget(self.preview_label)
        
        # Métriques
        metrics_layout = QHBoxLayout()
        
        duration_card = QFrame()
        duration_card.setStyleSheet("""
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 8px;
        """)
        duration_layout = QVBoxLayout(duration_card)
        duration_layout.addWidget(QLabel("45"), alignment=Qt.AlignmentFlag.AlignCenter)
        duration_layout.addWidget(QLabel("secondes"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        resolution_card = QFrame()
        resolution_card.setStyleSheet("""
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            padding: 8px;
        """)
        resolution_layout = QVBoxLayout(resolution_card)
        resolution_layout.addWidget(QLabel("1080x1920"), alignment=Qt.AlignmentFlag.AlignCenter)
        resolution_layout.addWidget(QLabel("pixels"), alignment=Qt.AlignmentFlag.AlignCenter)
        
        metrics_layout.addWidget(duration_card)
        metrics_layout.addWidget(resolution_card)
        
        preview_layout.addLayout(metrics_layout)
        layout.addWidget(preview_group)
        
        # Progression
        progress_group = QGroupBox("📊 Progression")
        progress_layout = QVBoxLayout(progress_group)
        
        progress_layout.addWidget(QLabel("Téléchargement TikTok :"))
        self.download_progress = AnimatedProgressBar()
        progress_layout.addWidget(self.download_progress)
        
        progress_layout.addWidget(QLabel("Upload YouTube :"))
        self.upload_progress = AnimatedProgressBar()
        progress_layout.addWidget(self.upload_progress)
        
        layout.addWidget(progress_group)
        
        # Status
        status_group = QGroupBox("📝 Statut")
        self.status_layout = QVBoxLayout(status_group)
        
        self.add_status_card("Prêt à traiter une vidéo TikTok", "info")
        
        layout.addWidget(status_group)
        layout.addStretch()
        
        return widget
        
    def setup_demo_data(self):
        """Configure les données de démonstration"""
        # Données de test
        self.url_input.setText("https://www.tiktok.com/@example/video/1234567890")
        self.title_input.setText("Ma super vidéo TikTok")
        self.description_input.setPlainText("Une description automatiquement générée depuis TikTok\\n\\n#TikTok #Viral #Trending")
        self.tags_input.setText("tiktok, viral, trending, music")
        
        # Status initial
        self.url_status.setText("✅ URL TikTok valide")
        self.url_status.setStyleSheet("color: #10b981; font-size: 12px;")
        
    def demo_fetch_metadata(self):
        """Simule la récupération des métadonnées"""
        self.add_status_card("Récupération des métadonnées...", "info")
        
        # Simuler un délai
        QTimer.singleShot(1500, self.demo_metadata_fetched)
        
    def demo_metadata_fetched(self):
        """Simule la réception des métadonnées"""
        # Remplir les champs
        self.title_input.setText("🎵 Danse viral TikTok 2024")
        self.description_input.setPlainText("Nouvelle chorégraphie qui fait le buzz sur TikTok !\\n\\nMusique : Artiste - Chanson\\nHashtags : #dance #viral #tiktok #trending\\n\\nN'hésitez pas à reproduire cette danse et à me taguer ! 💃🕺")
        self.tags_input.setText("dance, viral, tiktok, trending, music, 2024")
        
        # Mettre à jour l'aperçu
        self.preview_label.setText("✅ Métadonnées récupérées\\n\\nTitre : Danse viral TikTok 2024\\nDurée : 45 secondes\\nRésolution : 1080x1920\\nFormat : Vertical (Shorts)")
        self.preview_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(16, 185, 129, 0.1),
                stop:1 rgba(16, 185, 129, 0.05));
            border: 2px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            color: #10b981;
            font-size: 14px;
            min-height: 150px;
        """)
        
        self.add_status_card("Métadonnées récupérées avec succès", "success")
        
    def demo_start_processing(self):
        """Simule le démarrage du traitement"""
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        
        self.add_status_card("Traitement démarré", "info")
        self.add_status_card("Téléchargement de la vidéo TikTok...", "info")
        
        # Animation de progression
        self.progress_timer = QTimer()
        self.progress_value = 0
        self.progress_phase = "download"
        
        def update_progress():
            self.progress_value += 3
            
            if self.progress_phase == "download":
                self.download_progress.setValue(min(self.progress_value, 100))
                if self.progress_value >= 100:
                    self.progress_phase = "upload"
                    self.progress_value = 0
                    self.add_status_card("Téléchargement terminé", "success")
                    self.add_status_card("Upload vers YouTube...", "info")
                    
            elif self.progress_phase == "upload":
                self.upload_progress.setValue(min(self.progress_value, 100))
                if self.progress_value >= 100:
                    self.progress_timer.stop()
                    self.demo_processing_finished()
        
        self.progress_timer.timeout.connect(update_progress)
        self.progress_timer.start(100)
        
    def demo_processing_finished(self):
        """Simule la fin du traitement"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        self.add_status_card("✅ Upload terminé avec succès !", "success")
        self.add_status_card("ID Vidéo: dQw4w9WgXcQ", "success")
        
        # Message de succès
        QMessageBox.information(self, "Succès", 
                              "Vidéo uploadée avec succès !\\n\\nID: dQw4w9WgXcQ\\n\\nVoulez-vous ouvrir la vidéo sur YouTube?")
        
    def demo_cancel_processing(self):
        """Simule l'annulation du traitement"""
        if hasattr(self, 'progress_timer'):
            self.progress_timer.stop()
            
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        self.download_progress.setValue(0)
        self.upload_progress.setValue(0)
        
        self.add_status_card("Traitement annulé", "warning")
        
    def add_status_card(self, message, card_type="info"):
        """Ajoute une carte de statut"""
        card = StatusCard(message, card_type)
        self.status_layout.addWidget(card)
        self.status_cards.append(card)
        
        # Limiter à 5 cartes
        if len(self.status_cards) > 5:
            old_card = self.status_cards.pop(0)
            self.status_layout.removeWidget(old_card)
            old_card.deleteLater()
            
    def open_url_dialog(self):
        """Ouvre un dialogue pour entrer une URL"""
        url, ok = QFileDialog.getOpenFileName(self, "Sélectionner un fichier URL", "", "Tous les fichiers (*.*)")
        if ok and url:
            self.url_input.setText(url)
            
    def show_preferences(self):
        """Affiche les préférences"""
        QMessageBox.information(self, "Préférences", "Fenêtre de préférences\\n(fonctionnalité en développement)")
        
    def show_about(self):
        """Affiche la fenêtre À propos"""
        QMessageBox.about(self, "À propos", 
                         "TikTok to YouTube Desktop\\n"
                         "Version 2.0.0\\n\\n"
                         "Application moderne de conversion TikTok vers YouTube\\n"
                         "avec interface PyQt6 et direction artistique sombre.\\n\\n"
                         "Développé avec ❤️ en Python")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TikTok to YouTube Desktop Demo")
    
    # Police moderne
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = FullDemoWindow()
    window.show()
    
    # Centrer la fenêtre
    screen = app.primaryScreen()
    if screen:
        screen_geometry = screen.geometry()
        window_geometry = window.geometry()
        x = (screen_geometry.width() - window_geometry.width()) // 2
        y = (screen_geometry.height() - window_geometry.height()) // 2
        window.move(x, y)
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()