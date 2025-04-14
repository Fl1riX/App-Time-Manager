import psutil, sqlite3, logging, sys, time, threading, gui

from PyQt5.QtWidgets import QApplication, QDesktopWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
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
            main(i[0])
            time.sleep(300) 

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
            gui.show_error(f"Процесс '{name}' не найден.")
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
        gui.show_error(f"Процесс '{name}' не найден.")
        
    except psutil.AccessDenied:
        logging.error(f"🚫 Нет доступа к процессу '{name}'.")
        gui.show_error(f"Нет доступа к процессу '{name}'.")

    except psutil.ZombieProcess:
        logging.error(f"⚰️ Процесс '{name}' стал зомби.")
        gui.show_error(f"Процесс '{name}' стал зомби.")

    except Exception as e:
        logging.error(f"❌ Неизвестная ошибка: {e}")
        gui.show_error(f"Неизвестная ошибка: {e}")
        
class AppTimeManager:   
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.main_win = gui.MainWindow()
    
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