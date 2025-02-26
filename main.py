import psutil, sqlite3, logging, sys, time, threading

from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QWidget, QVBoxLayout, QPushButton, QDesktopWidget, QLabel, QLineEdit, QMessageBox
from PyQt5.QtCore import pyqtSignal
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    filename="manager_logs.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
    
def get_all_time():
    data = {}
    try:
        with sqlite3.connect("data.db") as con:
            cur = con.cursor()
            
            cur.execute("""SELECT name, date, MAX(CAST(time AS INT)) FROM data GROUP BY name, date""")
            result = cur.fetchall()
            
        logging.info(f"📊 Максимальное время за день: {result}")
        
        for name, _, max_time in result:
            data[name] = data.get(name, 0) + max_time

    except Exception as e:
        logging.error(f"❌ Ошибка при получении данных: {e}")
        return 0

    return data
                 
def today_time(name):
    with sqlite3.connect("data.db") as con:
        cur = con.cursor()
        today = datetime.now().date() 
        cur.execute("SELECT MAX(CAST(time AS INT)) FROM data WHERE date=? and name=? ", (str(today), name,))

        result = cur.fetchone()
    
    return result

def get_tracked_apps():
    with sqlite3.connect("data.db") as con: 
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS data (name TEXT, date TEXT, time INTEGER)""")
        con.commit()
        
        cur.execute("""SELECT name FROM data""")
        result = list(set(cur.fetchall()))
        
    return result
        
def tracking_loop():
    while True:
        for i in get_tracked_apps():
            #print("Вызов main()")
            main(i[0])
            time.sleep(300) 

def show_error(message):
    error_win = QMessageBox()
    error_win.setIcon(QMessageBox.Critical)
    error_win.setWindowTitle("Ошибка")
    error_win.setText(message)
    error_win.setStandardButtons(QMessageBox.Ok)
    error_win.exec_()

def main(name):
    try:
        min_time_list = []

        logging.info(f"🔍 Поиск процесса: {name}")

        # Поиск процесса по имени
        for p in psutil.process_iter(['name']):
            if p.info['name'] == name:
                # Извлечение времени старта процесса
                start_time_str = str(p).split("started=")[1].split("'")[1]

                # Преобразование времени старта в минуты
                start_time = int(start_time_str.split(":")[0]) * 60 + int(start_time_str.split(":")[1])

                min_time_list.append(start_time)

        if not min_time_list:
            logging.warning(f"⚠️ Процесс '{name}' не найден.")
            show_error(f"Процесс '{name}' не найден.")
            return

        start_time = min(min_time_list)
        logging.info(f"✅ Процесс '{name}' найден. Время старта: {start_time} минут от начала суток.")

        # Получение текущего времени в минутах
        now_time_sp = str(datetime.now()).split(" ")[1].split(":")
        now_time = int(now_time_sp[0]) * 60 + int(now_time_sp[1])

        # Подсчет времени работы приложения
        min_app_time = now_time - start_time

        try:
            with sqlite3.connect("data.db") as con:
                cur = con.cursor()

                time_str = f"{min_app_time} мин"
                cur.execute("""SELECT * FROM data WHERE name=? AND date=?""", (name, datetime.now().date(),))
                record_exists = cur.fetchall()
                
                if record_exists:
                    cur.execute("""UPDATE data SET time=? WHERE name=? AND date=?""", (time_str, name, datetime.now().date()))
                else:
                    cur.execute("""INSERT INTO data (name, time, date) VALUES (?, ?, ?)""", (name, time_str, datetime.now().date()))
                    
                con.commit()

                logging.info(f"💾 Данные записаны: {name}, {time_str}")

        except sqlite3.Error as e:
            logging.error(f"❌ Ошибка SQLite: {e}")

    except psutil.NoSuchProcess:
        logging.error(f"❌ Процесс '{name}' не найден.")
        show_error(f"Процесс '{name}' не найден.")
        
    except psutil.AccessDenied:
        logging.error(f"🚫 Нет доступа к процессу '{name}'.")
        show_error(f"Нет доступа к процессу '{name}'.")

    except psutil.ZombieProcess:
        logging.error(f"⚰️ Процесс '{name}' стал зомби.")
        show_error(f"Процесс '{name}' стал зомби.")

    except Exception as e:
        logging.error(f"❌ Неизвестная ошибка: {e}")
        show_error(f"Неизвестная ошибка: {e}")


"""APP GUI"""
class InfoWindow(QWidget):
    deleted = pyqtSignal()
    def __init__(self, title):
        logging.info(f"Открыта информация о {title}")
        super().__init__()
        
        data = get_all_time()
        
        self.setWindowTitle(title)
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout()
        
        #Текст с информацией
        if data != 0:
            self.delete = QPushButton("Удалить")
            self.delete.setStyleSheet("QPushButton { color: white; font-size: 15px}")
            self.delete.clicked.connect(lambda: (self.delete_app(title)))

            if today_time(title)[0] != None:
                self.label = QLabel(f"Общее время: {data[title]} мин\nВремя за сегодня: {today_time(title)[0]} мин")
            else:
                self.label = QLabel(f"Общее время: {data[title]} мин\nВремя за сегодня: 0 мин")
                
            self.label.setStyleSheet("QLabel { color: white; font-size: 15px}")
            layout.addWidget(self.label)
            layout.addWidget(self.delete)
            self.setLayout(layout)
        else:
            sys.exit()    
    
    def delete_app(self, name):
        with sqlite3.connect("data.db") as con:
            cur = con.cursor()  
            
            cur.execute("""DELETE FROM data WHERE name=?""", (name,))
            con.commit()
            
        self.deleted.emit()
        self.close()
        
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
    th = threading.Thread(target=tracking_loop, daemon=True)
    th.start()
    
    app_manager = AppTimeManager()
    app_manager.run()