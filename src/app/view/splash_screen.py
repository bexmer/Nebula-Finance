from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSequentialAnimationGroup
from PySide6.QtGui import QFont

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nebula Finance")
        self.setFixedSize(300, 300)

        # --- Configuración de la Ventana ---
        # Hacemos la ventana sin bordes y siempre encima
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # --- Layout y Logo ---
        layout = QVBoxLayout(self)
        self.logo_label = QLabel("NF")
        logo_font = QFont("Segoe UI", 80, QFont.Weight.Bold)
        self.logo_label.setFont(logo_font)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("""
            background-color: #232533;
            color: #8A9BFF;
            border: 8px solid #8A9BFF;
            border-radius: 125px; /* Mitad del tamaño del widget */
        """)
        self.logo_label.setFixedSize(250, 250)
        layout.addWidget(self.logo_label, 0, Qt.AlignmentFlag.AlignCenter)

        self.animation_group = None

    def start_animation(self, on_finished_callback):
        # Animación de opacidad (aparecer)
        fade_in = QPropertyAnimation(self, b"windowOpacity")
        fade_in.setDuration(800)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Animación de opacidad (desvanecer)
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(800)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Conectamos el final de la animación con la función que carga la ventana principal
        fade_out.finished.connect(on_finished_callback)

        # Agrupamos las animaciones para que se ejecuten en secuencia
        self.animation_group = QSequentialAnimationGroup()
        self.animation_group.addAnimation(fade_in)
        self.animation_group.addPause(1500) # Mantenemos el logo visible por 1.5 segundos
        self.animation_group.addAnimation(fade_out)

        self.animation_group.start()