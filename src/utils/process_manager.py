import subprocess
import psutil
import os
import sys
import ctypes
from typing import Optional, List, Tuple

class ProcessManager:
    @staticmethod
    def is_admin() -> bool:
        """Проверяет, запущен ли процесс от имени администратора"""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    @staticmethod
    def run_bat(bat_file: str, args: Optional[List[str]] = None, wait: bool = True, admin: bool = False) -> Tuple[int, str, str]:
        """
        Запускает .bat файл с указанными аргументами
        
        Args:
            bat_file: Путь к .bat файлу
            args: Список аргументов
            wait: Ждать ли завершения процесса
            admin: Запустить от имени администратора
            
        Returns:
            Tuple[returncode, stdout, stderr]
        """
        try:
            if not os.path.exists(bat_file):
                raise FileNotFoundError(f"Файл {bat_file} не найден")
                
            # Для bat-файлов используем cmd.exe
            cmd = ["cmd.exe", "/c", bat_file]
            if args:
                cmd.extend(args)
                
            if admin and not ProcessManager.is_admin():
                # Перезапускаем процесс от имени администратора
                try:
                    result = ctypes.windll.shell32.ShellExecuteW(
                        None,
                        "runas",
                        "cmd.exe",
                        f"/c \"{bat_file}\"",
                        os.path.dirname(bat_file),
                        1  # SW_SHOWNORMAL
                    )
                    
                    if result <= 32:  # Ошибка
                        return 1, "", f"Не удалось запустить процесс (код {result})"
                        
                    return 0, "", ""
                except Exception as e:
                    return 1, "", f"Ошибка запуска от администратора: {str(e)}"
                    
            # Обычный запуск
            if wait:
                # Запускаем с отображением консоли для bat-файлов
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.path.dirname(bat_file)
                )
                stdout, stderr = process.communicate()
                return process.returncode, stdout, stderr
            else:
                # Запускаем в фоне с отображением консоли
                process = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(bat_file),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
                return 0, "", ""
            
        except Exception as e:
            return 1, "", str(e)
    
    @staticmethod
    def is_process_running(process_name: str) -> bool:
        """Проверяет, запущен ли процесс с указанным именем"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() == process_name.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return False
    
    @staticmethod
    def kill_process(process_name: str) -> bool:
        """Завершает процесс с указанным именем"""
        try:
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'].lower() == process_name.lower():
                        proc.kill()
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return False
        except Exception:
            return False
    
    @staticmethod
    def get_winws_processes() -> List[dict]:
        """Возвращает список всех процессов winws.exe"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'status']):
            try:
                if proc.info['name'].lower() == 'winws.exe':
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'create_time': proc.info['create_time'],
                        'status': proc.info['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes 