import psutil, sqlite3, logging, sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidget, QWidget, QVBoxLayout, QPushButton, QDesktopWidget, QLabel
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    filename="manager_logs.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_inf_from_db():
    try:
        with sqlite3.connect("data.db") as con:
            cur = con.cursor()

            cur.execute("CREATE TABLE IF NOT EXISTS data (name TEXT, time TEXT, date TEXT)")
            con.commit()

            cur.execute("SELECT name, MAX(time) FROM data GROUP BY name")
            result = cur.fetchall()  
            logging.info(f"✅ Результаты из базы данных: {result}")

        return result
    except Exception as e:
        logging.error(f"❌ Ошибка в болучении данных из бд: {e}")
        return 0

def main(name):
    try:
        get_inf_from_db()
        
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

                time_str = f"{min_app_time} минут" if min_app_time < 60 else f"{round(min_app_time / 60, 2)} часа"
                cur.execute("INSERT INTO data (name, time, date) VALUES (?, ?, ?)", (name, time_str, datetime.now().replace(second=0, microsecond=0)))
                con.commit()

                logging.info(f"💾 Данные записаны: {name}, {time_str}")

        except sqlite3.Error as e:
            logging.error(f"❌ Ошибка SQLite: {e}")

    except psutil.NoSuchProcess:
        logging.error(f"❌ Процесс '{name}' не найден.")
        
    except psutil.AccessDenied:
        logging.error(f"🚫 Нет доступа к процессу '{name}'.")

    except psutil.ZombieProcess:
        logging.error(f"⚰️ Процесс '{name}' стал зомби.")

    except Exception as e:
        logging.error(f"❌ Неизвестная ошибка: {e}")

class InfoWindow(QWidget):
    def __init__(self, title):
        logging.info(f"Открыта информация о {title}")
        super().__init__()
        
        self.setWindowTitle(title)
        self.resize(400, 300)
        
        self.setStyleSheet("background-color: black;")
        
        layout = QVBoxLayout()
        
        self.label = QLabel("тут текст")
        self.label.setStyleSheet("QLabel { color: white; font-size: 15px}")
        
        layout.addWidget(self.label)
        
        self.setLayout(layout)
        
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("App Time Manager")
        self.resize(800, 500)
        
        self.setStyleSheet("background-color: black;")
        
        central_widget = QWidget()
        
        layout = QVBoxLayout()
        
        self.text_list = QListWidget()
        self.text_list.itemClicked.connect(self.on_item_clicked)
        
        if get_inf_from_db() != 0:
            for i in get_inf_from_db():
                self.text_list.addItems([str(i).split(",")[0].split("'")[1]])
        else:
            sys.exit()
            logging.error("❌ Ошибка при получении информации из бд, закрытие приложения.")
            
        self.text_list.setStyleSheet("QListWidget { color: white; font-size: 15px}")
        self.setCentralWidget(central_widget)
        
        self.add_btn = QPushButton("Add")
        self.add_btn.setStyleSheet("QPushButton { color: white; font-size: 15px}")
        self.add_btn.clicked.connect(lambda:print("Button pressed!"))
        
        layout.addWidget(self.text_list)
        layout.addWidget(self.add_btn)
        central_widget.setLayout(layout)
        
    def on_item_clicked(self, item):
        self.inf_win = InfoWindow(item.text())
        self.inf_win.show()

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
    main("Code.exe")
    
    app_manager = AppTimeManager()
    app_manager.run()