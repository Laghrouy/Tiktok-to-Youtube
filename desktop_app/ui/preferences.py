"""
Fenêtre de préférences pour personnaliser l'application
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QWidget, QLabel, QComboBox, QCheckBox, QSpinBox,
                            QPushButton, QGroupBox, QColorDialog, QSlider,
                            QFormLayout, QLineEdit, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPalette

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config, get_available_themes, get_theme

class PreferencesDialog(QDialog):
    """Fenêtre de préférences de l'application"""
    
    preferences_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Préférences")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        layout = QVBoxLayout(self)
        
        # Onglets
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Onglet Apparence
        self.create_appearance_tab()
        
        # Onglet Comportement  
        self.create_behavior_tab()
        
        # Onglet Traitement
        self.create_processing_tab()
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Appliquer")
        self.apply_btn.clicked.connect(self.apply_settings)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.ok_btn)
        
        layout.addLayout(buttons_layout)
        
        # Style de la fenêtre
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a0a, stop:1 #1a1a2e);
                color: #ffffff;
            }
            
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
            
            QGroupBox {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin: 10px 0;
                padding-top: 15px;
                font-weight: bold;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #8b5cf6;
            }
            
            QLabel {
                color: #ffffff;
            }
            
            QComboBox, QSpinBox, QLineEdit {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                padding: 8px;
                color: #ffffff;
            }
            
            QCheckBox {
                color: #ffffff;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid rgba(255, 255, 255, 0.3);
                background: rgba(255, 255, 255, 0.05);
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #8b5cf6, stop:1 #06b6d4);
                border: 1px solid #8b5cf6;
            }
            
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #8b5cf6, stop:1 #7c3aed);
                border: none;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7c3aed, stop:1 #8b5cf6);
            }
        """)
        
    def create_appearance_tab(self):
        """Crée l'onglet Apparence"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Thème
        theme_group = QGroupBox("Thème")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        themes = get_available_themes()
        for theme_id, theme_name in themes:
            self.theme_combo.addItem(theme_name, theme_id)
        theme_layout.addRow("Thème :", self.theme_combo)
        
        layout.addWidget(theme_group)
        
        # Groupe Police
        font_group = QGroupBox("Police")
        font_layout = QFormLayout(font_group)
        
        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems([
            "Segoe UI", "SF Pro Display", "Inter", "Roboto", 
            "Arial", "Helvetica", "Ubuntu", "System"
        ])
        font_layout.addRow("Famille :", self.font_family_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 20)
        self.font_size_spin.setSuffix(" px")
        font_layout.addRow("Taille :", self.font_size_spin)
        
        layout.addWidget(font_group)
        
        # Groupe Effets
        effects_group = QGroupBox("Effets visuels")
        effects_layout = QVBoxLayout(effects_group)
        
        self.animations_check = QCheckBox("Activer les animations")
        self.transparency_check = QCheckBox("Activer la transparence")
        
        effects_layout.addWidget(self.animations_check)
        effects_layout.addWidget(self.transparency_check)
        
        layout.addWidget(effects_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Apparence")
        
    def create_behavior_tab(self):
        """Crée l'onglet Comportement"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Automatisation
        auto_group = QGroupBox("Automatisation")
        auto_layout = QVBoxLayout(auto_group)
        
        self.auto_fetch_check = QCheckBox("Récupérer automatiquement les métadonnées")
        self.auto_shorts_check = QCheckBox("Détecter automatiquement les Shorts")
        self.remember_settings_check = QCheckBox("Se souvenir des derniers paramètres")
        
        auto_layout.addWidget(self.auto_fetch_check)
        auto_layout.addWidget(self.auto_shorts_check)
        auto_layout.addWidget(self.remember_settings_check)
        
        layout.addWidget(auto_group)
        
        # Groupe Fenêtre
        window_group = QGroupBox("Comportement de la fenêtre")
        window_layout = QVBoxLayout(window_group)
        
        self.minimize_tray_check = QCheckBox("Réduire dans la barre système")
        self.close_tray_check = QCheckBox("Fermer dans la barre système")
        
        window_layout.addWidget(self.minimize_tray_check)
        window_layout.addWidget(self.close_tray_check)
        
        layout.addWidget(window_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Comportement")
        
    def create_processing_tab(self):
        """Crée l'onglet Traitement"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe Paramètres par défaut
        defaults_group = QGroupBox("Paramètres par défaut")
        defaults_layout = QFormLayout(defaults_group)
        
        self.default_privacy_combo = QComboBox()
        self.default_privacy_combo.addItems(["public", "unlisted", "private"])
        defaults_layout.addRow("Visibilité :", self.default_privacy_combo)
        
        self.default_category_combo = QComboBox()
        categories = ["Entertainment", "Music", "Gaming", "Education", "Science & Technology", 
                     "Sports", "People & Blogs", "Comedy", "News & Politics", "Howto & Style"]
        self.default_category_combo.addItems(categories)
        defaults_layout.addRow("Catégorie :", self.default_category_combo)
        
        layout.addWidget(defaults_group)
        
        # Groupe Traitement
        processing_group = QGroupBox("Options de traitement")
        processing_layout = QVBoxLayout(processing_group)
        
        self.auto_normalize_check = QCheckBox("Normaliser l'audio automatiquement")
        self.auto_remux_check = QCheckBox("Optimiser les fichiers (remux)")
        
        processing_layout.addWidget(self.auto_normalize_check)
        processing_layout.addWidget(self.auto_remux_check)
        
        # Uploads simultanés
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("Uploads simultanés :"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 5)
        concurrent_layout.addWidget(self.concurrent_spin)
        concurrent_layout.addStretch()
        
        processing_layout.addLayout(concurrent_layout)
        
        layout.addWidget(processing_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Traitement")
        
    def load_current_settings(self):
        """Charge les paramètres actuels"""
        # Apparence
        current_theme = config.get('appearance', 'theme', 'dark')
        for i in range(self.theme_combo.count()):
            if self.theme_combo.itemData(i) == current_theme:
                self.theme_combo.setCurrentIndex(i)
                break
                
        self.font_family_combo.setCurrentText(config.get('appearance', 'font_family', 'Segoe UI'))
        self.font_size_spin.setValue(config.get('appearance', 'font_size', 14))
        self.animations_check.setChecked(config.get('appearance', 'animations_enabled', True))
        self.transparency_check.setChecked(config.get('appearance', 'transparency_enabled', True))
        
        # Comportement
        self.auto_fetch_check.setChecked(config.get('behavior', 'auto_fetch_metadata', True))
        self.auto_shorts_check.setChecked(config.get('behavior', 'auto_detect_shorts', True))
        self.remember_settings_check.setChecked(config.get('behavior', 'remember_last_settings', True))
        self.minimize_tray_check.setChecked(config.get('behavior', 'minimize_to_tray', False))
        self.close_tray_check.setChecked(config.get('behavior', 'close_to_tray', False))
        
        # Traitement
        self.default_privacy_combo.setCurrentText(config.get('processing', 'default_privacy', 'public'))
        self.default_category_combo.setCurrentText(config.get('processing', 'default_category', 'Entertainment'))
        self.auto_normalize_check.setChecked(config.get('processing', 'auto_normalize_audio', False))
        self.auto_remux_check.setChecked(config.get('processing', 'auto_remux', True))
        self.concurrent_spin.setValue(config.get('processing', 'concurrent_uploads', 1))
        
    def apply_settings(self):
        """Applique les paramètres"""
        # Apparence
        config.set('appearance', 'theme', self.theme_combo.currentData())
        config.set('appearance', 'font_family', self.font_family_combo.currentText())
        config.set('appearance', 'font_size', self.font_size_spin.value())
        config.set('appearance', 'animations_enabled', self.animations_check.isChecked())
        config.set('appearance', 'transparency_enabled', self.transparency_check.isChecked())
        
        # Comportement  
        config.set('behavior', 'auto_fetch_metadata', self.auto_fetch_check.isChecked())
        config.set('behavior', 'auto_detect_shorts', self.auto_shorts_check.isChecked())
        config.set('behavior', 'remember_last_settings', self.remember_settings_check.isChecked())
        config.set('behavior', 'minimize_to_tray', self.minimize_tray_check.isChecked())
        config.set('behavior', 'close_to_tray', self.close_tray_check.isChecked())
        
        # Traitement
        config.set('processing', 'default_privacy', self.default_privacy_combo.currentText())
        config.set('processing', 'default_category', self.default_category_combo.currentText())
        config.set('processing', 'auto_normalize_audio', self.auto_normalize_check.isChecked())
        config.set('processing', 'auto_remux', self.auto_remux_check.isChecked())
        config.set('processing', 'concurrent_uploads', self.concurrent_spin.value())
        
        # Sauvegarder
        config.save()
        
        # Émettre le signal
        self.preferences_changed.emit()
        
    def accept_settings(self):
        """Applique et ferme"""
        self.apply_settings()
        self.accept()