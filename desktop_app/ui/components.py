"""
Composants UI personnalisés pour l'application TikTok to YouTube
"""

from PyQt6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QProgressBar, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QPen
import math

class GradientProgressBar(QProgressBar):
    """Barre de progression avec dégradé animé"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTextVisible(True)
        self.setRange(0, 100)
        self.setValue(0)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()

        # Fond homogène sombre + bordure
        painter.setBrush(QColor(21, 21, 21))  # #151515
        painter.setPen(QPen(QColor(38, 38, 38), 1))  # #262626
        painter.drawRoundedRect(rect, 8, 8)

        # Barre de progression (dégradé conservé)
        if self.maximum() > 0 and self.value() > 0:
            progress_ratio = max(0.0, min(1.0, self.value() / float(self.maximum())))
            progress_width = max(0, int(progress_ratio * (rect.width() - 2)))
            if progress_width > 0:
                gradient = QLinearGradient(0, 0, progress_width, 0)
                gradient.setColorAt(0, QColor(139, 92, 246))  # primary
                gradient.setColorAt(0.5, QColor(6, 182, 212))  # secondary
                gradient.setColorAt(1, QColor(236, 72, 153))  # accent

                painter.setBrush(gradient)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect.adjusted(1, 1, -rect.width() + 1 + progress_width, -1), 6, 6)

        # Texte
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.value()}%")

class AnimatedButton(QPushButton):
    """Bouton avec animations au survol"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._glow_radius = 0
        self.setFixedHeight(50)
        
        # Animation de brillance
        self.glow_animation = QPropertyAnimation(self, b"glow_radius")
        self.glow_animation.setDuration(300)
        self.glow_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    @pyqtProperty(int)
    def glow_radius(self):
        return self._glow_radius
    
    @glow_radius.setter
    def glow_radius(self, value):
        self._glow_radius = value
        self.update()
    
    def enterEvent(self, event):
        self.glow_animation.setStartValue(0)
        self.glow_animation.setEndValue(15)
        self.glow_animation.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.glow_animation.setStartValue(15)
        self.glow_animation.setEndValue(0)
        self.glow_animation.start()
        super().leaveEvent(event)

class StatusCard(QFrame):
    """Carte d'état avec icône et message"""
    
    def __init__(self, title="", message="", status_type="info", parent=None):
        super().__init__(parent)
        self.setObjectName("status_card")
        self.setupUI(title, message, status_type)
        
    def setupUI(self, title, message, status_type):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(20, 16, 20, 16)
        
        # Titre
        title_label = QLabel(title)
        title_label.setObjectName("card_title")
        title_label.setStyleSheet("""
            #card_title {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 4px;
            }
        """)
        
        # Message
        message_label = QLabel(message)
        message_label.setObjectName("card_message")
        message_label.setWordWrap(True)
        message_label.setStyleSheet("""
            #card_message {
                color: #a1a1aa;
                font-size: 14px;
                line-height: 1.4;
            }
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(message_label)
        
        # Style selon le type
        colors = {
            'info': '#8b5cf6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#ef4444'
        }
        
        color = colors.get(status_type, colors['info'])
        self.setStyleSheet(f"""
            #status_card {{
                background-color: #121212;
                border: 1px solid #262626;
                border-left: 4px solid {color};
                border-radius: 12px;
            }}
        """)

class LoadingSpinner(QWidget):
    """Spinner de chargement animé"""
    
    def __init__(self, size=32, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.setFixedSize(size, size)
        
        # Timer pour l'animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.rotate)
        
    def start(self):
        self.timer.start(50)  # 20 FPS
        self.show()
        
    def stop(self):
        self.timer.stop()
        self.hide()
        
    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Centre du widget
        center_x = self.width() // 2
        center_y = self.height() // 2
        
        # Dessiner les arcs
        for i in range(12):
            angle = self.angle + i * 30
            opacity = 1.0 - (i * 0.08)
            
            painter.save()
            painter.translate(center_x, center_y)
            painter.rotate(angle)
            
            # Couleur avec opacité dégradée
            color = QColor(139, 92, 246)  # primary
            color.setAlphaF(opacity)
            painter.setPen(QPen(color, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            
            # Ligne
            painter.drawLine(0, -self.size//2 + 4, 0, -self.size//2 + 12)
            painter.restore()

class GlowingFrame(QFrame):
    """Frame avec effet de brillance"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.glow_color = QColor(139, 92, 246, 100)  # primary avec alpha
        
    def set_glow_color(self, color):
        self.glow_color = color
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Effet de brillance
        for i in range(3):
            painter.setPen(QPen(self.glow_color, 2 - i))
            painter.drawRoundedRect(self.rect().adjusted(i, i, -i, -i), 12 - i, 12 - i)
        
        super().paintEvent(event)

class ImagePreview(QLabel):
    """Widget de prévisualisation d'image avec placeholder"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("image_preview")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(300, 200)
        self.setStyleSheet("""
            #image_preview {
                background-color: #111111;
                border: 1px solid #262626;
                border-radius: 12px;
                color: #71717a;
                font-size: 14px;
            }
        """)
        self.setText("Aperçu de la vidéo TikTok\\nSera affiché ici après téléchargement")

class MetricsCard(QFrame):
    """Carte pour afficher des métriques"""
    
    def __init__(self, title="", value="", unit="", parent=None):
        super().__init__(parent)
        self.setObjectName("metrics_card")
        self.setupUI(title, value, unit)
        
    def setupUI(self, title, value, unit):
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # Valeur
        value_layout = QHBoxLayout()
        value_label = QLabel(str(value))
        value_label.setObjectName("metric_value")
        unit_label = QLabel(unit)
        unit_label.setObjectName("metric_unit")
        
        value_layout.addWidget(value_label)
        value_layout.addWidget(unit_label)
        value_layout.addStretch()
        
        # Titre
        title_label = QLabel(title)
        title_label.setObjectName("metric_title")
        
        layout.addLayout(value_layout)
        layout.addWidget(title_label)
        
        self.setStyleSheet("""
            #metrics_card {
                background-color: #121212;
                border: 1px solid #262626;
                border-radius: 12px;
            }
            #metric_value {
                color: #ffffff;
                font-size: 24px;
                font-weight: bold;
            }
            #metric_unit {
                color: #a1a1aa;
                font-size: 14px;
                font-weight: 500;
            }
            #metric_title {
                color: #71717a;
                font-size: 12px;
                font-weight: 500;
            }
        """)
    
    def update_value(self, value, unit=""):
        # Mettre à jour la valeur affichée
        value_label = self.findChild(QLabel, "metric_value")
        unit_label = self.findChild(QLabel, "metric_unit")
        if value_label:
            value_label.setText(str(value))
        if unit_label and unit:
            unit_label.setText(unit)