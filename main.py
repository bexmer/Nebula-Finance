import sys
import os

# --- INICIO DE LA SOLUCIÓN ---
# 1. Le decimos explícitamente a pyqtgraph que use PySide6.
#    Esto debe ocurrir ANTES de que cualquier otra parte del código
#    intente importar pyqtgraph.
os.environ['PYQTGRAPH_QT_LIB'] = 'PySide6'
# --- FIN DE LA SOLUCIÓN ---

# --- Configuración de la Ruta ---
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_path)

# --- Importaciones de la Aplicación ---
from PySide6.QtWidgets import QApplication
from app.view.main_window import MainWindow
from app.controller.app_controller import AppController
from app.database.db_manager import initialize_database

# --- Punto de Entrada Principal ---
if __name__ == "__main__":
    initialize_database()
    print("Database initialized and tables created if they didn't exist.")

    app = QApplication(sys.argv)
    window = MainWindow()
    
    controller = AppController(window)
    window.set_controller(controller)

    window.dashboard_page.set_default_month_filter()
    controller.update_dashboard()
    
    window.show()
    sys.exit(app.exec())

