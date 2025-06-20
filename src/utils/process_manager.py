import ctypes
import os
import subprocess
import sys
import re

class ServiceManager:
    def __init__(self, service_name="zapret", winsw_path="bin/winws.exe"):
        self.service_name = service_name
        self.winsw_path = os.path.abspath(winsw_path)
        self.winsw_dir = os.path.dirname(self.winsw_path)

    def is_admin(self):
        """Проверяет, запущены ли скрипты с правами администратора."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def run_as_admin(self):
        """Перезапускает приложение с правами администратора."""
        if sys.platform == 'win32':
            try:
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            except Exception as e:
                print(f"Failed to elevate privileges: {e}")
                return False
        return True

    def _run_command(self, command, as_admin=False):
        """Выполняет команду в консоли."""
        if as_admin and not self.is_admin():
            # This is a simplified approach. Real elevation for specific commands is complex.
            # For service management, the whole app should be elevated.
            print("Admin rights required.")
            return None, "Admin rights required."

        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE # Hide console window

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                shell=True,
                cwd=self.winsw_dir,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            stdout, stderr = process.communicate()
            return stdout.decode('utf-8', errors='ignore'), stderr.decode('utf-8', errors='ignore')
        except Exception as e:
            return None, str(e)

    def get_service_status(self):
        """Получает статус службы: 'RUNNING', 'STOPPED', 'NOT_FOUND'."""
        stdout, stderr = self._run_command(f'sc query "{self.service_name}"')
        if stdout:
            if "RUNNING" in stdout:
                return "RUNNING"
            elif "STOPPED" in stdout:
                return "STOPPED"
            elif "failed" in stderr or "1060" in stdout: # 1060: The specified service does not exist
                return "NOT_FOUND"
        return "UNKNOWN"

    def install_service(self, bat_file_path):
        """Устанавливает службу, парся аргументы из .bat файла."""
        args = self._parse_bat_file(bat_file_path)
        if not args:
            return False, "Failed to parse .bat file."
            
        # Commands to install the service
        self.uninstall_service() # Ensure it's not installed first
        
        install_cmd = (
            f'sc create "{self.service_name}" binPath= "{self.winsw_path} {args}" '
            f'DisplayName= "{self.service_name}" start= auto'
        )
        
        stdout, stderr = self._run_command(install_cmd, as_admin=True)
        if not stdout or "SUCCESS" not in stdout:
            return False, f"Failed to create service: {stderr}"

        desc_cmd = f'sc description "{self.service_name}" "Zapret DPI bypass software"'
        self._run_command(desc_cmd, as_admin=True)
        
        return self.start_service()

    def uninstall_service(self):
        """Удаляет службу."""
        self._run_command(f'sc stop "{self.service_name}"', as_admin=True)
        stdout, stderr = self._run_command(f'sc delete "{self.service_name}"', as_admin=True)
        if (stdout and "SUCCESS" in stdout) or (stderr and "1060" in stderr): # 1060 means not found, which is ok
            return True, "Service uninstalled successfully."
        return False, f"Failed to uninstall service: {stderr}"

    def start_service(self):
        """Запускает службу."""
        stdout, stderr = self._run_command(f'sc start "{self.service_name}"', as_admin=True)
        if stdout and ("START_PENDING" in stdout or "RUNNING" in stdout):
            return True, "Service started successfully."
        # Check if it's already running
        status_out, _ = self._run_command(f'sc query "{self.service_name}"')
        if status_out and "RUNNING" in status_out:
            return True, "Service is already running."
        return False, f"Failed to start service: {stderr or stdout}"

    def stop_service(self):
        """Останавливает службу."""
        stdout, stderr = self._run_command(f'sc stop "{self.service_name}"', as_admin=True)
        if stdout and ("STOP_PENDING" in stdout or "SUCCESS" in stdout):
            return True, "Service stopped successfully."
        status_out, _ = self._run_command(f'sc query "{self.service_name}"')
        if status_out and "STOPPED" in status_out:
            return True, "Service is already stopped."
        return False, f"Failed to stop service: {stderr or stdout}"

    def restart_service(self):
        """Перезапускает службу."""
        stop_ok, stop_msg = self.stop_service()
        if stop_ok:
            import time
            time.sleep(1) # Give it a moment to stop
            return self.start_service()
        return False, f"Failed to stop service for restart: {stop_msg}"
        
    def _parse_bat_file(self, bat_path):
        """
        Парсит .bat файл, чтобы извлечь аргументы для winws.exe,
        в точности повторяя логику из service.bat.
        """
        try:
            with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading bat file: {e}")
            return None

        capture = False
        raw_args_line = ""
        winsw_executable_name = "winws.exe"

        # Находим строку, содержащую вызов winws.exe
        for line in lines:
            if winsw_executable_name in line.lower():
                # Начинаем захват с этой строки
                capture = True
                # Отсекаем все до winws.exe включительно
                raw_args_line = line[line.lower().find(winsw_executable_name) + len(winsw_executable_name):]
                break
        
        if not capture:
            return None

        # Очищаем строку от лишних символов в начале и в конце
        raw_args_line = raw_args_line.strip()

        # Заменяем переменные окружения из .bat на их Python-эквиваленты
        # %~dp0 -> директория .bat файла
        bat_dir = os.path.dirname(os.path.abspath(bat_path))
        raw_args_line = raw_args_line.replace("%~dp0", f'"{bat_dir}\\"')

        # %BIN% -> абсолютный путь к директории bin
        bin_dir = os.path.abspath(self.winsw_dir)
        raw_args_line = raw_args_line.replace("%%BIN%%", f'"{bin_dir}\\"').replace("%BIN%", f'"{bin_dir}\\"')
        
        # %LISTS% -> абсолютный путь к директории lists
        lists_dir = os.path.abspath(os.path.join(bin_dir, "..", "lists"))
        raw_args_line = raw_args_line.replace("%%LISTS%%", f'"{lists_dir}\\"').replace("%LISTS%", f'"{lists_dir}\\"')
        
        # Заменяем двойные кавычки на одинарные для внутреннего разделения,
        # чтобы split работал корректно. Используем редкий символ как временный разделитель.
        # Это упрощенный подход по сравнению с логикой в service.bat, но более надежный в Python.
        # re.split будет обрабатывать строки в кавычках как единое целое.
        
        # Имитация сложного парсинга аргументов из bat файла
        # Это более простой и надежный способ, чем посимвольный перебор в .bat
        args = []
        # Используем regex для разделения по пробелам, но сохраняя строки в кавычках
        for arg in re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', raw_args_line):
            arg = arg.strip()
            if not arg:
                continue

            # Убираем лишние кавычки по краям, если они есть
            if arg.startswith('"') and arg.endswith('"'):
                arg = arg[1:-1]
            
            # В service.bat есть специальная обработка для @-файлов
            if arg.startswith('@'):
                # Заменяем @ на полный путь
                arg = f'"{os.path.abspath(os.path.join(bat_dir, arg[1:]))}"'

            # В service.bat есть обработка для путей без кавычек
            # Здесь мы предполагаем, что пути с пробелами уже в кавычках.
            # Для надежности обернем все, что похоже на путь, но не имеет кавычек
            elif ("/" in arg or "\\" in arg) and not arg.startswith('"'):
                 arg = f'"{arg}"'

            args.append(arg)

        final_args = " ".join(args)
        
        # В `service.bat` используется сложная замена кавычек для `sc create`.
        # `binPath` требует экранирования внутренних кавычек с помощью \".
        # Формируем binPath так, чтобы он был заключен в кавычки, а внутренние были экранированы.
        final_args = final_args.replace('"', '\\"')

        return final_args 