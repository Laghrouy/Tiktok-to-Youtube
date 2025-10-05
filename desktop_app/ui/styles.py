"""
Styles et thèmes pour l'application TikTok to YouTube
Inspiré par une direction artistique moderne avec des dégradés et couleurs sombres
"""

DARK_THEME = {
    'background': '#0a0a0a',
    'surface': '#1a1a1a',
    'surface_variant': '#2a2a2a',
    'primary': '#8b5cf6',  # Violet
    'primary_dark': '#7c3aed',
    'secondary': '#06b6d4',  # Cyan
    'accent': '#ec4899',  # Rose
    'text_primary': '#ffffff',
    'text_secondary': '#a1a1aa',
    'text_muted': '#71717a',
    'success': '#10b981',
    'warning': '#f59e0b',
    'error': '#ef4444',
    'border': '#374151',
    'hover': '#3f3f46'
}

def get_main_stylesheet():
    """Retourne le stylesheet principal de l'application"""
    return f"""
    /* Fenêtre principale */
    QMainWindow {{
        background-color: #000000;
        color: {DARK_THEME['text_primary']};
    }}
    
    /* Widget central */
    QWidget {{
        background-color: #000000;
        color: {DARK_THEME['text_primary']};
        font-family: 'Segoe UI', 'SF Pro Display', 'Inter', sans-serif;
        font-size: 14px;
    }}
    
    /* Frame principal avec effet de verre */
    #main_frame {{
        background-color: #111111;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        margin: 20px;
    }}
    
    /* Titre principal */
    #title_label {{
        font-size: 32px;
        font-weight: bold;
        color: {DARK_THEME['primary']};
        background: none;
        border: none;
        padding: 20px 0;
    }}
    
    /* Cards/GroupBox */
    QGroupBox {{
        background-color: #121212;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        margin: 10px;
        padding-top: 20px;
        font-weight: 600;
        font-size: 16px;
        color: {DARK_THEME['text_primary']};
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 15px;
        padding: 5px 15px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary']},
            stop:1 {DARK_THEME['secondary']});
        border-radius: 8px;
        color: white;
        font-weight: bold;
    }}
    
    /* Champs de saisie */
    QLineEdit {{
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        color: {DARK_THEME['text_primary']};
        min-height: 20px;
    }}
    
    QLineEdit:focus {{
        border: 2px solid {DARK_THEME['primary']};
        background: rgba(139, 92, 246, 0.1);
    }}
    
    QLineEdit:hover {{
        border: 1px solid #2e2e2e;
        background-color: #171717;
    }}
    
    /* Zone de texte */
    QTextEdit {{
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 12px;
        font-size: 14px;
        color: {DARK_THEME['text_primary']};
    }}
    
    QTextEdit:focus {{
        border: 2px solid {DARK_THEME['primary']};
        background: rgba(139, 92, 246, 0.1);
    }}
    
    /* ComboBox */
    QComboBox {{
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 12px 16px;
        font-size: 14px;
        color: {DARK_THEME['text_primary']};
        min-height: 20px;
    }}
    
    QComboBox:hover {{
        border: 1px solid #2e2e2e;
        background-color: #171717;
    }}
    
    QComboBox::drop-down {{
        border: none;
        background: transparent;
        width: 30px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 8px solid {DARK_THEME['text_secondary']};
        margin-right: 10px;
    }}
    
    QComboBox QAbstractItemView {{
        background-color: #111111;
        border: 1px solid #262626;
        border-radius: 8px;
        color: {DARK_THEME['text_primary']};
        selection-background-color: {DARK_THEME['primary']};
    }}
    
    /* Boutons */
    QPushButton {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary']},
            stop:1 {DARK_THEME['primary_dark']});
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: bold;
        font-size: 14px;
        padding: 12px 24px;
        min-height: 20px;
    }}
    
    QPushButton:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary_dark']},
            stop:1 {DARK_THEME['primary']});
    }}
    
    QPushButton:pressed {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #6d28d9,
            stop:1 #5b21b6);
    }}
    
    QPushButton:disabled {{
        background: rgba(255, 255, 255, 0.1);
        color: {DARK_THEME['text_muted']};
    }}
    
    /* Bouton secondaire */
    #secondary_button {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['secondary']},
            stop:1 #0891b2);
    }}
    
    #secondary_button:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #0891b2,
            stop:1 {DARK_THEME['secondary']});
    }}
    
    /* Bouton de danger */
    #danger_button {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['error']},
            stop:1 #dc2626);
    }}
    
    #danger_button:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #dc2626,
            stop:1 {DARK_THEME['error']});
    }}
    
    /* Bouton de succès */
    #success_button {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['success']},
            stop:1 #059669);
    }}
    
    #success_button:hover {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 #059669,
            stop:1 {DARK_THEME['success']});
    }}
    
    /* CheckBox */
    QCheckBox {{
        color: {DARK_THEME['text_primary']};
        font-size: 14px;
        spacing: 8px;
    }}
    
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background: rgba(255, 255, 255, 0.05);
    }}
    
    QCheckBox::indicator:hover {{
        border: 2px solid {DARK_THEME['primary']};
        background: rgba(139, 92, 246, 0.1);
    }}
    
    QCheckBox::indicator:checked {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {DARK_THEME['primary']},
            stop:1 {DARK_THEME['primary_dark']});
        border: 2px solid {DARK_THEME['primary']};
    }}
    
    /* Barres de progression */
    QProgressBar {{
        background-color: #151515;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        text-align: center;
        color: {DARK_THEME['text_primary']};
        font-weight: bold;
        height: 24px;
    }}
    
    QProgressBar::chunk {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary']},
            stop:0.5 {DARK_THEME['secondary']},
            stop:1 {DARK_THEME['accent']});
        border-radius: 6px;
        margin: 1px;
    }}
    
    /* Labels */
    QLabel {{
        color: {DARK_THEME['text_primary']};
        font-size: 14px;
    }}
    
    #subtitle_label {{
        color: {DARK_THEME['text_secondary']};
        font-size: 16px;
        font-weight: 500;
    }}
    
    #status_label {{
        color: {DARK_THEME['text_secondary']};
        font-size: 14px;
        padding: 8px 12px;
        background-color: #111111;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }}
    
    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: #0f0f0f;
        width: 12px;
        border-radius: 6px;
        margin: 0;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: #2a2a2a;
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: #333333;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    /* Onglets */
    QTabWidget::pane {{
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        background-color: #121212;
    }}
    
    QTabBar::tab {{
        background-color: #171717;
        color: {DARK_THEME['text_secondary']};
        padding: 12px 20px;
        margin: 0 2px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        font-weight: 500;
    }}
    
    QTabBar::tab:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary']},
            stop:1 {DARK_THEME['secondary']});
        color: white;
        font-weight: bold;
    }}
    
    QTabBar::tab:hover:!selected {{
        background: rgba(255, 255, 255, 0.08);
        color: {DARK_THEME['text_primary']};
    }}
    
    /* Table/Liste */
    QTableWidget {{
        background-color: #111111;
        border: 1px solid #262626;
        border-radius: 8px;
        gridline-color: #262626;
        color: {DARK_THEME['text_primary']};
    }}
    
    QTableWidget::item {{
        padding: 8px;
        border: none;
    }}
    
    QTableWidget::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary']},
            stop:1 rgba(139, 92, 246, 0.7));
    }}
    
    QHeaderView::section {{
        background-color: #171717;
        color: {DARK_THEME['text_primary']};
        padding: 12px;
        border: none;
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        font-weight: bold;
    }}

    /* Menus */
    QMenuBar {{
        background-color: #0f0f0f;
        border-bottom: 1px solid #262626;
        padding: 4px;
    }}
    QMenuBar::item {{
        background: transparent;
        padding: 8px 16px;
        border-radius: 6px;
        color: {DARK_THEME['text_primary']};
    }}
    QMenuBar::item:selected {{
        background-color: #171717;
    }}
    QMenu {{
        background-color: #0f0f0f;
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 8px;
        color: {DARK_THEME['text_primary']};
    }}
    QMenu::item {{
        padding: 8px 16px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: #171717;
    }}
    
    /* Tooltip */
    QToolTip {{
        background: {DARK_THEME['surface']};
        color: {DARK_THEME['text_primary']};
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 12px;
    }}

    /* ===================== Extensions pour homogénéité ===================== */
    /* Éditeur de texte brut */
    QPlainTextEdit {{
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 12px;
        padding: 12px;
        font-size: 14px;
        color: {DARK_THEME['text_primary']};
    }}

    QPlainTextEdit:focus {{
        border: 2px solid {DARK_THEME['primary']};
        background: rgba(139, 92, 246, 0.08);
    }}

    /* Listes et vues */
    QListWidget, QListView, QTreeView {{
        background-color: #111111;
        border: 1px solid #262626;
        border-radius: 8px;
        color: {DARK_THEME['text_primary']};
        outline: 0;
    }}

    QListWidget::item, QListView::item {{
        padding: 8px 10px;
    }}

    QListWidget::item:selected, QListView::item:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {DARK_THEME['primary']},
            stop:1 rgba(139, 92, 246, 0.7));
        color: white;
    }}

    QListWidget::item:hover:!selected, QListView::item:hover:!selected {{
        background-color: #171717;
    }}

    /* Zones de scroll génériques */
    QAbstractScrollArea {{
        background-color: #111111;
        border-radius: 8px;
    }}

    QAbstractScrollArea::corner {{
        background-color: #111111;
    }}

    QScrollArea {{
        background-color: #111111;
        border: 1px solid #262626;
        border-radius: 8px;
    }}

    /* Séparateur */
    QSplitter::handle {{
        background-color: #171717;
        border: 1px solid #262626;
        margin: 0px;
    }}

    /* Radio buttons */
    QRadioButton {{
        color: {DARK_THEME['text_primary']};
        font-size: 14px;
        spacing: 8px;
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 9px;
        border: 2px solid rgba(255, 255, 255, 0.3);
        background-color: #141414;
    }}

    QRadioButton::indicator:hover {{
        border: 2px solid {DARK_THEME['primary']};
        background: rgba(139, 92, 246, 0.1);
    }}

    QRadioButton::indicator:checked {{
        border: 6px solid {DARK_THEME['primary']};
        background-color: #141414;
    }}

    /* Slider */
    QSlider::groove:horizontal {{
        height: 6px;
        background: #262626;
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {DARK_THEME['primary']};
        width: 14px;
        height: 14px;
        margin: -5px 0; /* centrer */
        border-radius: 7px;
    }}

    QSlider::handle:horizontal:hover {{
        background: {DARK_THEME['primary_dark']};
    }}

    /* ToolButton */
    QToolButton {{
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 8px;
        color: {DARK_THEME['text_primary']};
        padding: 6px 10px;
    }}

    QToolButton:hover {{
        background-color: #171717;
    }}

    QToolButton:checked {{
        background-color: #1a1a1a;
        border-color: {DARK_THEME['primary']};
    }}

    /* SpinBox */
    QSpinBox {{
        background-color: #141414;
        border: 1px solid #262626;
        border-radius: 8px;
        padding: 6px 8px;
        color: {DARK_THEME['text_primary']};
    }}

    QSpinBox::up-button, QSpinBox::down-button {{
        background: transparent;
        border: none;
        width: 16px;
    }}

    QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
        background-color: #171717;
        border-radius: 6px;
    }}
    """

def get_glow_effect_style(color="#8b5cf6", radius=20):
    """Retourne un style pour effet de brillance"""
    return f"""
    border: 2px solid {color};
    """

def get_card_style(elevated=False):
    """Retourne un style pour les cartes"""
    return f"""
    background-color: #121212;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 15px;
    """