# main.py

import sys
import os

os.environ['PYQTGRAPH_QT_LIB'] = 'PySide6'

src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_path)

from PySide6.QtWidgets import QApplication
from app.view.main_window import MainWindow
from app.view.splash_screen import SplashScreen # Importamos la nueva clase
from app.controller.app_controller import AppController
from app.database.db_manager import initialize_database

def show_main_window():
    """Función que crea y muestra la ventana principal."""
    global window # Hacemos la ventana una variable global para que no sea eliminada

    initialize_database()

    window = MainWindow()
    controller = AppController(window)
    window.set_controller(controller)

    window.dashboard_page.set_default_month_filter()
    controller.update_dashboard()

    window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. Crear y mostrar la pantalla de carga
    splash = SplashScreen()
    splash.show()

    # 2. Iniciar la animación y decirle qué hacer cuando termine
    #    La función show_main_window se ejecutará y luego la splash se cerrará
    splash.start_animation(on_finished_callback=lambda: (show_main_window(), splash.close()))

    sys.exit(app.exec())