from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect

class Notification(QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("NotificationLabel")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
        self.hide()

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_animation)

        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(300)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.finished.connect(self._on_animation_finished)
        self._is_hiding = False

    def show_message(self, message, message_type='success'):
        self.timer.stop()
        self.animation.stop()
        self._is_hiding = False

        self.setText(message)
        self.setProperty("message_type", "success" if message_type == 'success' else 'error')
        self.style().unpolish(self); self.style().polish(self)
        self.show_animation()

    def show_animation(self):
        parent_width = self.parent().width()
        self.setFixedWidth(int(parent_width * 0.4))
        self.adjustSize()
        
        start_pos = QRect((parent_width - self.width()) // 2, self.parent().height(), self.width(), self.height())
        end_pos = QRect(start_pos.x(), self.parent().height() - self.height() - 20, self.width(), self.height())
        
        self.setGeometry(start_pos)
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        
        self.show()
        self.animation.start()
        self.timer.start(5000)

    def hide_animation(self):
        self._is_hiding = True
        start_pos = self.geometry()
        end_pos = QRect(start_pos.x(), self.parent().height(), self.width(), self.height())
        
        self.animation.setStartValue(start_pos)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def _on_animation_finished(self):
        if self._is_hiding:
            self.hide()

