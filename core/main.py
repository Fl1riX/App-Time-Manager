import getpass
import logging
import os
import shutil
import sys
import time
import psutil

from datetime import datetime
from pyqadmin import admin

import ui.main_win as main_win
import ui.helpers as helpers
import core.database as database

# The `logging.basicConfig()` function call in the provided Python code snippet is configuring the
# root logger for the logging module. Here's a breakdown of the parameters used in this call:
logging.basicConfig(
    level=logging.INFO,
    filename="manager_logs.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s - %(levelname)s - %(message)s"
)
    
#! TODO: напоминание отдохнуть и возможность ставить цель по времени 
        
def tracking_loop():
    while True:
        for i in database.get_tracked_apps():
            main(i[0])
            time.sleep(300) 

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

#!ERROR: ищется только 1 процесс, а все остальные нет. если удалить и добавить, то время обновиться

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
            helpers.show_error(f"Процесс '{name}' не найден.")
            return

        start_time = min(min_time_list)
        logging.info(f"✅ Процесс '{name}' найден. Время старта: {start_time} минут от начала суток.")

        # Получение текущего времени в минутах
        now_time_sp = str(datetime.now()).split(" ")[1].split(":")
        now_time = int(now_time_sp[0]) * 60 + int(now_time_sp[1])

        # Подсчет времени работы приложения
        min_app_time = now_time - start_time

        database.write_app_time(min_app_time, name)

    except psutil.NoSuchProcess:
        logging.error(f"❌ Процесс '{name}' не найден.")
        main_win.show_error(f"Процесс '{name}' не найден.")
        
    except psutil.AccessDenied:
        logging.error(f"🚫 Нет доступа к процессу '{name}'.")
        main_win.show_error(f"Нет доступа к процессу '{name}'.")

    except psutil.ZombieProcess:
        logging.error(f"⚰️ Процесс '{name}' стал зомби.")
        main_win.show_error(f"Процесс '{name}' стал зомби.")

    except Exception as e:
        logging.error(f"❌ Неизвестная ошибка: {e}")
        main_win.show_error(f"Неизвестная ошибка: {e}")
        