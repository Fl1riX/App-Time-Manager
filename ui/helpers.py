from PyQt5.QtWidgets import QMessageBox

def show_error(message):
    error_win = QMessageBox()
    error_win.setIcon(QMessageBox.Critical)
    error_win.setWindowTitle("Ошибка")
    error_win.setText(message)
    error_win.setStandardButtons(QMessageBox.Ok)
    error_win.exec_()