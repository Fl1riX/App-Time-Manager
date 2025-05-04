import psutil
import sqlite3
import logging
import sys
import time
import threading
import shutil
import getpass
import os
import gui

from PyQt5.QtWidgets import QApplication, QDesktopWidget
from pyqadmin import admin
from datetime import datetime

# The `logging.basicConfig()` function call in the provided Python code snippet is configuring the
# root logger for the logging module. Here's a breakdown of the parameters used in this call:
logging.basicConfig(
    level=logging.INFO,
    filename="manager_logs.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
    
def get_all_time():
    """
    The function `get_all_time` retrieves the maximum time spent per day for each name from a SQLite
    database and returns a dictionary with the total time spent by each name.
    :return: A dictionary containing the total maximum time for each unique name in the database is
    being returned.
    """
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
            
def write_app_time(time, name):
    try:
        with sqlite3.connect("data.db") as con:
            cur = con.cursor()
            time_str = f"{time} мин"
            cur.execute("""SELECT * FROM data WHERE name=? AND date=?""", (name, datetime.now().date(),))
            
            
            if cur.fetchall():
                cur.execute("""UPDATE data SET time=? WHERE name=? AND date=?""", (time_str, name, datetime.now().date()))
            else:
                cur.execute("""INSERT INTO data (name, time, date) VALUES (?, ?, ?)""", (name, time_str, datetime.now().date()))
                
            con.commit()
            logging.info(f"💾 Данные записаны: {name}, {time_str}")
    except sqlite3.Error as e:
        logging.error(f"❌ Ошибка SQLite: {e}")


@admin
def add_to_startup():
    """
    This Python function adds the current executable file to the Windows startup folder for automatic
    execution on system boot.
    """
    try:
        file_path = sys.executable
        file_name = os.path.basename(file_path)
        startup_path = f"C:/Users/{getpass.getuser()}/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup/{file_name }"

        if not os.path.exists(startup_path):
            shutil.copy(file_path, startup_path, follow_symlinks=True)
            logging.info("✅ Исполняемый файл был добавлен в автозагрузку! ✅")
        else: 
            logging.info("✅ Исполняемый файл уже был добавлен в автозагрузку! ✅")
    except Exception as e:
        logging.error(f"❌ Ошибка при добавлении в автозагрузку: {e} ❌")

def main(name):
    """
    This Python function searches for a process by name, calculates its running time, and stores the
    data in a SQLite database, handling various exceptions along the way.
    
    :param name: The `name` parameter in the `main` function is used to specify the name of the process
    you want to search for and track its start time and running duration. The function will search for a
    process with the given name, calculate the time it has been running, and store this information in a
    :return: The `main` function does not explicitly return any value. However, it contains multiple
    return statements within conditional blocks. The function can return early with `return` statements
    in case the process is not found, there is an error, or if an exception is caught. If none of these
    conditions are met, the function will reach the end and implicitly return `None`.
    """
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

        write_app_time(min_app_time, name)
    

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
        
# The `AppTimeManager` class initializes a PyQt application with a main window and provides a method
# to center the window and run the application.
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
    #starting main thread
    main_th = threading.Thread(target=tracking_loop, daemon=True)
    main_th.start()
    
    add_to_startup()
    
    app_manager = AppTimeManager()
    app_manager.run()