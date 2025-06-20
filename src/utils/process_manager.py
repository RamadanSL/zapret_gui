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
        self.manual_process_pid = None

    def is_admin(self):
        """Проверяет, запущены ли скрипты с правами администратора."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False

    def relaunch_as_admin(self):
        """Перезапускает текущий скрипт с правами администратора."""
        if sys.platform == 'win32':
            try:
                # Используем PowerShell для запроса повышения прав, как в service.bat
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
                return True
            except Exception as e:
                print(f"Failed to elevate privileges: {e}")
                return False
        return False

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
        if args is None: # Проверяем на None, т.к. пустая строка аргументов может быть валидной
            return False, "Failed to parse .bat file or winws.exe not found in it."
            
        # Commands to install the service
        self.uninstall_service() # Ensure it's not installed first
        
        # Правильное формирование binPath для sc create.
        # Весь путь + аргументы должны быть одной строкой в кавычках,
        # а все внутренние кавычки должны быть экранированы.
        full_bin_path = f'"{self.winsw_path}" {args}'
        escaped_bin_path = full_bin_path.replace('"', '\\"')

        install_cmd = (
            f'sc create "{self.service_name}" binPath= "{escaped_bin_path}" '
            f'DisplayName= "{self.service_name}" start= auto'
        )
        
        stdout, stderr = self._run_command(install_cmd, as_admin=True)
        if not stdout or "SUCCESS" not in stdout:
            return False, f"Failed to create service: {stderr or 'Unknown error'}. Command: {install_cmd}"

        desc_cmd = f'sc description "{self.service_name}" "Zapret DPI bypass software"'
        self._run_command(desc_cmd, as_admin=True)
        
        return self.start_service()

    def uninstall_service(self):
        """
        Удаляет службу 'zapret', а также связанные службы 'WinDivert'.
        """
        services_to_remove = [self.service_name, "WinDivert", "WinDivert14"]
        all_successful = True
        error_messages = []

        for service in services_to_remove:
            # Сначала останавливаем службу
            self._run_command(f'sc stop "{service}"', as_admin=True)
            
            # Затем удаляем
            stdout, stderr = self._run_command(f'sc delete "{service}"', as_admin=True)
            
            # Успехом считаем либо сообщение SUCCESS, либо ошибку 1060 (служба не найдена)
            if (stdout and "SUCCESS" in stdout) or (stderr and "1060" in stderr):
                continue
            else:
                all_successful = False
                error_messages.append(f"Failed to uninstall service '{service}': {stderr}")
        
        if all_successful:
            return True, "Все службы (zapret, WinDivert) успешно удалены."
        else:
            return False, "\n".join(error_messages)

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
        Парсит .bat файл, чтобы извлечь ЧИСТУЮ строку аргументов для winws.exe,
        в точности повторяя логику из service.bat.
        Возвращает строку аргументов без экранирования.
        """
        try:
            with open(bat_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading bat file: {e}")
            return None

        raw_args_line = ""
        winsw_executable_name = "winws.exe"

        for line in lines:
            lower_line = line.lower()
            if winsw_executable_name in lower_line:
                raw_args_line = line[lower_line.find(winsw_executable_name) + len(winsw_executable_name):]
                break
        
        if not raw_args_line:
            return None # winws.exe не найден

        raw_args_line = raw_args_line.strip()
        if not raw_args_line:
            return "" # winws.exe найден, но аргументов нет

        # Замена переменных окружения .bat на их Python-эквиваленты
        base_dir = os.path.dirname(os.path.abspath(self.winsw_path))
        bat_dir = os.path.dirname(os.path.abspath(bat_path))
        
        # Создаем словарь замен
        replacements = {
            "%~dp0": f'"{bat_dir}\\"',
            "%%BIN%%": f'"{base_dir}\\"',
            "%BIN%": f'"{base_dir}\\"',
            "%%LISTS%%": f'"{os.path.join(base_dir, "..", "lists")}\\"',
            "%LISTS%": f'"{os.path.join(base_dir, "..", "lists")}\\"',
        }

        for var, value in replacements.items():
            raw_args_line = raw_args_line.replace(var, value)
            
        # Просто возвращаем обработанную строку. Экранированием займется install_service.
        return raw_args_line.strip() 

    def get_service_start_type(self):
        """Получает тип запуска службы: 'AUTO', 'DEMAND', 'DISABLED', 'NOT_FOUND'."""
        stdout, stderr = self._run_command(f'sc qc "{self.service_name}"')
        if "1060" in stderr or (stdout and "failed" in stdout.lower()):
            return "NOT_FOUND"
        if stdout:
            for line in stdout.splitlines():
                if "START_TYPE" in line:
                    if "AUTO_START" in line:
                        return "AUTO"
                    elif "DEMAND_START" in line:
                        return "DEMAND"
                    elif "DISABLED" in line:
                        return "DISABLED"
        return "UNKNOWN"

    def set_service_start_type(self, start_type: str):
        """Устанавливает тип запуска службы ('auto' или 'demand')."""
        if start_type not in ["auto", "demand"]:
            return False, "Invalid start type specified."
        
        stdout, stderr = self._run_command(f'sc config "{self.service_name}" start= {start_type}', as_admin=True)
        if stdout and "SUCCESS" in stdout:
            return True, f"Тип запуска службы изменен на '{start_type}'."
        return False, f"Не удалось изменить тип запуска: {stderr}"

    def start_manual_process(self, bat_path):
        """Запускает .bat файл в новой консоли и сохраняет его PID."""
        try:
            # CREATE_NEW_CONSOLE ensures it runs in its own window
            process = subprocess.Popen(['cmd.exe', '/c', bat_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            self.manual_process_pid = process.pid
            return True, f"Процесс запущен с PID: {self.manual_process_pid}"
        except Exception as e:
            return False, f"Не удалось запустить процесс: {e}"

    def stop_manual_process(self):
        """Останавливает процесс, запущенный вручную."""
        if not self.manual_process_pid:
            return False, "Нет информации о запущенном вручную процессе."
        
        # /F - force, /T - terminate child processes
        stdout, stderr = self._run_command(f"taskkill /F /T /PID {self.manual_process_pid}")
        if stdout and "SUCCESS" in stdout:
            self.manual_process_pid = None
            return True, "Процесс успешно остановлен."
        
        # Если процесс уже был закрыт вручную
        if stderr and ("not found" in stderr.lower() or "128" in stderr):
             self.manual_process_pid = None
             return True, "Процесс не был найден (возможно, уже закрыт)."
        
        return False, f"Не удалось остановить процесс: {stderr}"

    def is_manual_process_running(self):
        """Проверяет, активен ли еще процесс, запущенный вручную."""
        if not self.manual_process_pid:
            return False
        
        stdout, _ = self._run_command(f'tasklist /FI "PID eq {self.manual_process_pid}"')
        if stdout and str(self.manual_process_pid) in stdout:
            return True
        else:
            # Если процесс не найден, сбрасываем PID
            self.manual_process_pid = None
            return False 