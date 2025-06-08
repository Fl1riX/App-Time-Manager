import logging
import sqlite3
from datetime import datetime

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
        
