import sys
import os

os.environ['PYQTGRAPH_QT_LIB'] = 'PySide6'

src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.append(src_path)

from PySide6.QtWidgets import QApplication
from app.view.main_window import MainWindow
from app.controller.app_controller import AppController
from app.database.db_manager import initialize_database

if __name__ == "__main__":
    initialize_database()

    app = QApplication(sys.argv)
    window = MainWindow()
    
    controller = AppController(window)
    window.set_controller(controller)

    window.dashboard_page.set_default_month_filter()
    controller.update_dashboard()
    
    window.show()
    sys.exit(app.exec())