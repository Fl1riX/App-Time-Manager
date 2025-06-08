import threading
import sys

from PyQt5.QtWidgets import QApplication, QDesktopWidget

#import ui.main_win as main_win
from ui import MainWindow
from core import tracking_loop, add_to_startup

# The `AppTimeManager` class initializes a PyQt application with a main window and provides a method
# to center the window and run the application.
class AppTimeManager:   
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_win = MainWindow()
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def run(self):
        self.main_win.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    main_th = threading.Thread(target=tracking_loop, daemon=True)
    main_th.start()
    
    add_to_startup()
    
    app_manager = AppTimeManager()
    app_manager.run()