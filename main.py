import psutil, sqlite3, logging, sys

from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5 import QtWidgets
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    filename="manager_logs.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def find_proc(name):
    try:
        min_time_list = []
        pid_list = []

        logging.info(f"🔍 Поиск процесса: {name}")

        # Поиск процесса по имени
        for p in psutil.process_iter(['name']):
            if p.info['name'] == name:
                # Извлечение времени старта процесса
                start_time_str = str(p).split("started=")[1].split("'")[1]
                pid_str = str(p).split("pid=")[1].split(",")[0]

                # Преобразование времени старта в минуты
                start_time = int(start_time_str.split(":")[0]) * 60 + int(start_time_str.split(":")[1])

                pid_list.append(pid_str)
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
        pid = pid_list[min_time_list.index(start_time)]
        app_path = psutil.Process(int(pid)).exe()

        try:
            with sqlite3.connect("data.db") as con:
                cur = con.cursor()
                cur.execute("CREATE TABLE IF NOT EXISTS data (name TEXT, time TEXT, path TEXT)")
                con.commit()

                time_str = f"{min_app_time} минут" if min_app_time < 60 else f"{round(min_app_time / 60, 2)} часа"
                cur.execute("INSERT INTO data (name, time, path) VALUES (?, ?, ?)", (name, time_str, app_path))
                con.commit()

                logging.info(f"💾 Данные записаны: {name}, {time_str}, {app_path}")

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("App Time Manager")
        self.setGeometry(500, 150, 800, 500)

class AppTimeManager:   
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_win = MainWindow()
    
    def run(self):
        self.main_win.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    find_proc("Code.exe")
    
    app_manager = AppTimeManager()
    app_manager.run()
