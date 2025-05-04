import logging
import sqlite3
import sys

from PyQt5.QtWidgets import QMainWindow, QListWidget, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QMessageBox
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import pyqtSignal, Qt
from main import get_all_time, today_time, main

def show_error(message):
    error_win = QMessageBox()
    error_win.setIcon(QMessageBox.Critical)
    error_win.setWindowTitle("Ошибка")
    error_win.setText(message)
    error_win.setStandardButtons(QMessageBox.Ok)
    error_win.exec_()

# This class represents an information window in a PyQt application that displays data and a graph for
# a specific application, with the ability to delete the application's data.
class InfoWindow(QWidget):
    deleted = pyqtSignal()
    
    def __init__(self, title):
        logging.info(f"Открыта информация о {title}")
        super().__init__()
        
        data = get_all_time()
        layout = QVBoxLayout(self)
        
        self.setWindowTitle(title)
        self.setMinimumSize(600, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: black;}
            QLabel {
                color: white;
                font-size: 15px;
                background-color: transparent;
                padding: 5px;}
            QPushButton {
                color: white;
                background-color: #000000;
                font-size: 15px;
                padding: 5px;
                border: 1px solid #fafafa;
                border-radius: 5px;}
        """)
        
        self.no_schedule = QLabel("Не достаточно данных для постоения графика")
        
        if data != 0:
            fig = Figure(facecolor='black', figsize=(2, 4))
            ax = fig.add_subplot(facecolor='black')
            fig.subplots_adjust()
            dates, minutes = self.schedule(title)
            if len(dates) > 1:
                ax.bar(dates, minutes, color='blue')

                # Настройка текста графика
                ax.set_xlabel("Дата", color='white')
                ax.set_ylabel("Минут", color='white')
                ax.tick_params(axis='both', colors='white')
                
            elif len(dates) == 1:
                layout.addWidget(self.no_schedule)

            canvas = FigureCanvasQTAgg(fig)
            layout.addWidget(canvas)
            
            # Текст с информацией
            if data[title] < 60:
                self.label = QLabel(f"Общее время: {data[title]} мин\n")
            else:
                self.label = QLabel(f"Общее время: {round(data[title]/60, 2)}ч\n")
            
            layout.addWidget(self.label)
            
            today = today_time(title)[0]
            if today < 60:
                self.label2 = QLabel(f"Время за сегодня: {today} мин")
            else:
                self.label2 = QLabel(f"Время за сегодня: {round(today/60, 2)}ч")
                
            layout.addWidget(self.label2)

            self.delete_btn = QPushButton("Удалить")
            self.delete_btn.setFixedSize(100, 30)
            self.delete_btn.clicked.connect(lambda: self.delete_app(title))
            layout.addWidget(self.delete_btn, alignment=Qt.AlignCenter)
        else:
            self.close()   

    def delete_app(self, name):
        """
        The function `delete_app` deletes a record from a SQLite database based on the provided name and
        emits a signal before closing.
        
        :param name: The `delete_app` function takes two parameters:
        """
        with sqlite3.connect("data.db") as con:
            cur = con.cursor()  
            
            cur.execute("""DELETE FROM data WHERE name=?""", (name,))
            con.commit()
            
        self.deleted.emit()
        self.close()
        
    #Создание графика 
    @staticmethod
    def schedule(app):
        """
        The `schedule` static method retrieves the dates and times of the most recent 5 entries for a
        given app from a SQLite database.
        
        :param app: The `app` parameter in the `schedule` method is used to specify the name of the
        application for which you want to retrieve scheduling information. This method connects to a
        SQLite database, retrieves the most recent 5 entries for the specified application name from the
        `data` table, and then extracts the
        :return: The `schedule` method is returning two lists: `dates` and `times`. The `dates` list
        contains the date strings retrieved from the database for a specific application (specified by
        the `app` parameter), and the `times` list contains the integer values extracted from the time
        strings after splitting them.
        """
        with sqlite3.connect("data.db") as con:
            cur = con.cursor()
            
            cur.execute("""SELECT * FROM data WHERE name=? ORDER BY date DESC LIMIT 5""", (app,))
            con.commit()
            
            result = list(cur.fetchall())
            
        dates = []
        times = []
        
        for _, date_str, time_str in result:
            dates.append(date_str)
            times.append(int(time_str.split(" ")[0]))  
            
        return dates, times
        
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