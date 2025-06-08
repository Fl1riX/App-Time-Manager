import logging
import sys

from PyQt5.QtWidgets import QMainWindow, QListWidget, QWidget, QVBoxLayout, QPushButton, QLineEdit
from .info_win import InfoWindow
from core import get_all_time, main
        
# The `MainWindow` class in Python creates a GUI window for an app time manager with features to track
# and add applications.
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("App Time Manager")
        self.setFixedSize(800, 500)
        self.setStyleSheet("background-color: black;")
        
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        #Список отслеживаемых приложений
        self.text_list = QListWidget()
        self.text_list.itemClicked.connect(lambda item: self.on_item_clicked(item))
        
        data = get_all_time()
        if data!= 0:
            self.refresh_list()
        else:
            logging.error("❌ Ошибка при получении информации из бд, закрытие приложения.")
            sys.exit()
            
        self.text_list.setStyleSheet("QListWidget { color: white; font-size: 15px}")
        self.setCentralWidget(central_widget)
        
        #Кнопка добавления приложения в отслеживаемые
        self.add_btn = QPushButton("Добавить")
        self.add_btn.setStyleSheet("QPushButton { color: white; font-size: 15px}")
        self.add_btn.clicked.connect(lambda:(self.track_app(), self.refresh_list(), self.entry.clear()))
        
        #Поле ввода текста
        self.entry = QLineEdit(self)
        self.entry.setPlaceholderText("Введите название процесса")
        self.entry.setStyleSheet("QLineEdit { color: white; font-size: 15px}")
        
        layout.addWidget(self.text_list)
        layout.addWidget(self.entry)
        layout.addWidget(self.add_btn)
        central_widget.setLayout(layout)
        
    def on_item_clicked(self, item):
        self.info_win = InfoWindow(item.text())
        self.info_win.deleted.connect(self.refresh_list)  # Связываем сигнал с обновлением списка
        self.info_win.show()
    
    def refresh_list(self): #обновляем список отслеживаемых приложений
        self.text_list.clear()
        data = get_all_time()
        self.text_list.addItems(data.keys())
    
    def track_app(self):
        name = self.entry.text()
        main(name)