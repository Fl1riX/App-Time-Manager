import customtkinter as tk
import psutil

from datetime import datetime

def find_proc(name):
    try:
        min_time_list = []
        pid_list = []

        #поиск процесса по имени
        for p in psutil.process_iter(['name']):
            if p.info['name'] == name:
                #извлечение времени старта процесса
                sp = str(p).split("started=")[1].split("'")[1]
                #извлечение  pid процесса
                pid_sp = (str(p).split("pid=")[1].split(","))
                pid_list.append(pid_sp[0])
                
                min_time_list.append(int(sp.split(":")[0]) * 60 + int(sp.split(":")[1]))
        
        start_time = min(min_time_list)

        #получение реального времени
        now_time_sp = str(datetime.now()).split(" ")[1].split(":")
        now_time = int(now_time_sp[0]) * 60 + int(now_time_sp[1])

        #получение времени, проведенного в приложении и запись в файл 
        min_app_time = now_time - start_time
        pid = pid_list[min_time_list.index(start_time)]
        
        if min_app_time > 60:
            app_time = round(min_app_time / 60, 2)
            
        with open("data.txt", "w", encoding='utf-8') as file:
            file.write(f"{name}:{app_time} часа:{pid}")
        print(f"{app_time} часа")
    
    except psutil.NoSuchProcess:
        print("Процесс не найден")
        
    except psutil.AccessDenied:
        print("Нет доступа к процессу")
        
    except psutil.ZombieProcess:
        print("Процесс стал зомби")
    
    except Exception as e:
        print(e)
        
def main_win():
    win = tk.CTk()
    win.geometry("800x600")
    win.resizable(0, 0)
    win.title("App Time Manager")
    
    
    
    

    win.mainloop()
    
if __name__ == "__main__":
    find_proc("Code.exe")
    main_win()





