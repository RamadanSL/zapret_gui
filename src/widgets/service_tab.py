import os
import sys
import ctypes
import subprocess
import tempfile
import time
from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QMessageBox, QLabel, QHBoxLayout, QGroupBox, QSizePolicy
from PySide6.QtCore import QThread, Signal, QObject, Qt, QTimer


class ServiceWorker(QObject):
    """
    Выполняет операции со службами Windows в отдельном потоке.
    """
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, service_name, bat_file_path, action, parent=None):
        super().__init__(parent)
        self.service_name = service_name
        self.bat_file_path = bat_file_path
        self.action = action
        
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.bin_path = os.path.join(self.base_path, 'bin')
        self.lists_path = os.path.join(self.base_path, 'lists')
        self.winws_path = os.path.join(self.bin_path, 'winws.exe')

    def run(self):
        """Запускает соответствующий метод в зависимости от действия."""
        try:
            if self.action == "install":
                self._install_service()
            elif self.action == "remove":
                self._remove_service()
            elif self.action == "start":
                self._start_service()
            elif self.action == "stop":
                self._stop_service()
        except Exception as e:
            self.error.emit(f"Произошла непредвиденная ошибка: {e}")

    def parse_bat_args(self):
        """
        Извлекает аргументы для winws.exe из указанного .bat-файла.
        """
        try:
            with open(self.bat_file_path, 'r', encoding='cp866') as f:
                lines = f.readlines()

            args = ""
            capture = False
            
            for line in lines:
                line = line.strip()
                
                if 'winws.exe' in line:
                    capture = True
                    if '"%BIN%winws.exe"' in line:
                        line = line.split('"%BIN%winws.exe"')[1]
                    elif 'winws.exe' in line:
                        line = line.split('winws.exe')[1]
                
                if capture:
                    if line.endswith('^'):
                        line = line[:-1].strip()
                        args += line + " "
                    else:
                        args += line + " "
                        break
            
            if not args.strip():
                return None

            # Заменяем переменные на полные пути БЕЗ добавления лишних кавычек
            args = args.replace('%BIN%', self.bin_path + '\\')
            args = args.replace('%LISTS%', self.lists_path + '\\')
            
            game_filter_flag_file = os.path.join(self.bin_path, 'game_filter.enabled')
            game_filter = "1024-65535" if os.path.exists(game_filter_flag_file) else "0"
            args = args.replace('%GameFilter%', game_filter)

            return args.strip()
        except Exception as e:
            print(f"Ошибка парсинга .bat файла: {e}")
            return None

    def _run_as_admin(self, commands):
        """
        Запускает команды с правами администратора через UAC, используя временный .bat файл.
        Команды с префиксом '@' будут проигнорированы в случае ошибки.
        """
        bat_file_path = None
        try:
            # Создаем временный .bat файл в текущей директории (`.`) чтобы избежать проблем с правами доступа
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.bat', encoding='cp866', dir='.') as bat_file:
                bat_file_path = bat_file.name
                bat_file.write('@echo off\n')
                
                for command in commands:
                    ignore_error = command.startswith('@')
                    if ignore_error:
                        command = command[1:]  # Убираем префикс
                        bat_file.write(f'{command}\n')
                    else:
                        # Если команда важна, проверяем ее результат.
                        # В случае ошибки - выходим из .bat файла.
                        bat_file.write(f'{command}\n')
                        bat_file.write('if errorlevel 1 exit /b %errorlevel%\n')

            ps_command = f'Start-Process "{bat_file_path}" -Verb RunAs -WindowStyle Hidden -Wait'
            result = subprocess.run(['powershell', '-Command', ps_command], capture_output=True, text=True, encoding='cp866', timeout=60)
            
            final_stderr = result.stderr if result.stderr.strip() else result.stdout

            return result.returncode == 0, result.stdout, final_stderr

        except subprocess.TimeoutExpired:
            return False, "", "Операция заняла слишком много времени (тайм-аут)."
        except Exception as e:
            return False, "", f"Критическая ошибка при запуске .bat файла: {e}"
        finally:
            if bat_file_path and os.path.exists(bat_file_path):
                time.sleep(0.2)
                try:
                    os.unlink(bat_file_path)
                except OSError as e:
                    print(f"Не удалось удалить временный файл {bat_file_path}: {e}")

    def _install_service(self):
        """Создает и запускает службу Windows."""
        if not os.path.exists(self.winws_path):
            self.error.emit(f"Ошибка: '{self.winws_path}' не найден.")
            return

        args = self.parse_bat_args()
        if args is None:
            self.error.emit(f"Не удалось извлечь аргументы из '{os.path.basename(self.bat_file_path)}'")
            return
        
        service_command = f'"{self.winws_path}" {args}'
        binpath_arg = f'binPath= "{service_command}"'
        
        install_commands = [
            # Используем '@' чтобы игнорировать ошибки, если служба не существует
            f'@sc stop {self.service_name}',
            f'@sc delete {self.service_name}',
            # Эти команды важны, при ошибке выполнение прервется
            f'sc create {self.service_name} {binpath_arg} DisplayName= "{self.service_name}" start= auto',
            f'sc start {self.service_name}'
        ]
        
        success, stdout, stderr = self._run_as_admin(install_commands)

        if success:
            self.finished.emit(f"Служба '{self.service_name}' успешно установлена и запущена.")
        else:
            error_message = f"Ошибка при установке службы:\n"
            if stderr: error_message += f"Stderr: {stderr}\n"
            if stdout: error_message += f"Stdout: {stdout}\n"
            self.error.emit(error_message)

    def _remove_service(self):
        """Останавливает и удаляет службу."""
        remove_commands = [
            # Используем '@' чтобы игнорировать ошибки, если служба не существует
            f'@sc stop {self.service_name}',
            f'@sc delete {self.service_name}',
            '@sc stop WinDivert',
            '@sc delete WinDivert',
            '@sc stop WinDivert14',
            '@sc delete WinDivert14'
        ]
        success, stdout, stderr = self._run_as_admin(remove_commands)
        
        # Для удаления не так важна ошибка, главное чтобы все выполнилось
        self.finished.emit(f"Операция удаления служб завершена.")

    def _start_service(self):
        """Запускает службу."""
        success, stdout, stderr = self._run_as_admin([f'sc start {self.service_name}'])
        if success:
            self.finished.emit(f"Служба '{self.service_name}' успешно запущена.")
        else:
            self.error.emit(f"Ошибка запуска службы '{self.service_name}': {stderr}")

    def _stop_service(self):
        """Останавливает службу."""
        success, stdout, stderr = self._run_as_admin([f'sc stop {self.service_name}'])
        if success:
            self.finished.emit(f"Служба '{self.service_name}' успешно остановлена.")
        else:
            # Игнорируем ошибку "не запущена"
            if "NOT_RUNNING" in stderr.upper() or "НЕ ЗАПУЩЕНА" in stderr.upper():
                 self.finished.emit(f"Служба '{self.service_name}' уже была остановлена.")
            else:
                self.error.emit(f"Ошибка остановки службы '{self.service_name}': {stderr}")


class ServiceTab(QWidget):
    """Вкладка для управления службами Windows."""
    
    def __init__(self, file_manager, process_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.process_manager = process_manager
        self.main_window = main_window
        self.worker = None
        self.worker_thread = None
        self.is_operation_in_progress = False
        self.init_ui()

    def get_button_style(self, button_type="default"):
        """Get button style based on type"""
        base_style = """
            QPushButton {
                padding: 10px 15px;
                border: 2px solid #cccccc;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
                min-width: 120px;
            }
            QPushButton:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #cccccc;
                border-color: #e0e0e0;
            }
        """
        
        color_styles = {
            "success": "QPushButton { background-color: #28a745; color: white; }",
            "danger": "QPushButton { background-color: #dc3545; color: white; }",
            "info": "QPushButton { background-color: #17a2b8; color: white; }",
            "warning": "QPushButton { background-color: #ffc107; color: #333333; }",
            "primary": "QPushButton { background-color: #6f42c1; color: white; }",
            "secondary": "QPushButton { background-color: #6c757d; color: white; }"
        }
        
        return base_style + color_styles.get(button_type, color_styles["secondary"])
    
    def get_group_style(self):
        """Get common group box style"""
        return """
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                padding-top: 10px;
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #f8f9fa;
                color: #333333;
                font-weight: bold;
            }
        """
    
    def get_label_style(self, status_type="default"):
        """Get label style based on status type"""
        base_style = """
            font-size: 12pt;
            font-weight: bold;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #dee2e6;
        """
        
        status_styles = {
            "success": "background-color: #d4edda; color: #155724; border-color: #c3e6cb;",
            "error": "background-color: #f8d7da; color: #721c24; border-color: #f5c6cb;",
            "warning": "background-color: #fff3cd; color: #856404; border-color: #ffeaa7;",
            "info": "background-color: #d1ecf1; color: #0c5460; border-color: #bee5eb;",
            "default": "background-color: #f8f9fa; color: #6c757d; border-color: #dee2e6;"
        }
        
        return base_style + status_styles.get(status_type, status_styles["default"])

    def init_ui(self):
        """Инициализирует пользовательский интерфейс вкладки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Группа управления файлами
        file_group = QGroupBox("Управление службой")
        file_group.setStyleSheet(self.get_group_style())
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(12)
        
        # Выбор файла
        file_combo_layout = QHBoxLayout()
        file_combo_layout.setSpacing(12)
        file_label = QLabel("Выберите .bat файл:")
        file_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        
        self.file_combo = QComboBox()
        self.file_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #cccccc;
                border-radius: 6px;
                background-color: #ffffff;
                font-size: 11pt;
            }
            QComboBox:hover {
                border-color: #0078d4;
            }
            QComboBox:focus {
                border-color: #0078d4;
            }
        """)
        file_combo_layout.addWidget(file_label)
        file_combo_layout.addWidget(self.file_combo)
        file_combo_layout.addStretch()
        
        # Кнопки управления службой
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.install_btn = QPushButton("📦 Установить")
        self.uninstall_btn = QPushButton("🗑️ Удалить")
        self.start_btn = QPushButton("▶ Запустить")
        self.stop_btn = QPushButton("⏹ Остановить")
        self.status_btn = QPushButton("📊 Статус")
        self.refresh_btn = QPushButton("🔄 Обновить")
        
        # Set button properties
        for btn in [self.install_btn, self.uninstall_btn, self.start_btn, self.stop_btn, self.status_btn, self.refresh_btn]:
            btn.setMinimumWidth(130)
            btn.setMinimumHeight(36)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Apply styles
        self.install_btn.setStyleSheet(self.get_button_style("success"))
        self.uninstall_btn.setStyleSheet(self.get_button_style("danger"))
        self.start_btn.setStyleSheet(self.get_button_style("info"))
        self.stop_btn.setStyleSheet(self.get_button_style("warning"))
        self.status_btn.setStyleSheet(self.get_button_style("primary"))
        self.refresh_btn.setStyleSheet(self.get_button_style("secondary"))
        
        btn_layout.addWidget(self.install_btn)
        btn_layout.addWidget(self.uninstall_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.status_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addStretch()
        
        file_layout.addLayout(file_combo_layout)
        file_layout.addLayout(btn_layout)
        
        # Статус службы
        status_group = QGroupBox("Статус службы")
        status_group.setStyleSheet(self.get_group_style())
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(12)
        self.status_label = QLabel("Статус: Неизвестно")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(36)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.status_label.setStyleSheet(self.get_label_style("default"))
        status_layout.addWidget(self.status_label)
        
        # Информация о службе
        info_group = QGroupBox("Информация о службе")
        info_group.setStyleSheet(self.get_group_style())
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        self.service_info = QLabel("Выберите файл для отображения информации о службе")
        self.service_info.setWordWrap(True)
        self.service_info.setMinimumHeight(48)
        self.service_info.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.service_info.setStyleSheet("""
            padding: 10px;
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            color: #6c757d;
        """)
        info_layout.addWidget(self.service_info)
        
        # Добавляем все группы в основной layout
        layout.addWidget(file_group)
        layout.addSpacing(8)
        layout.addWidget(status_group)
        layout.addSpacing(8)
        layout.addWidget(info_group)
        layout.addStretch()
        
        # Подключаем сигналы
        self.install_btn.clicked.connect(self.install_service)
        self.uninstall_btn.clicked.connect(self.remove_service)
        self.start_btn.clicked.connect(self.start_service)
        self.stop_btn.clicked.connect(self.stop_service)
        self.status_btn.clicked.connect(self.update_status)
        self.refresh_btn.clicked.connect(self.refresh_profiles)
        self.file_combo.currentTextChanged.connect(self.update_service_info)
        
        # Инициализация
        self.refresh_profiles()
        self.update_buttons_state()
        self.update_status()
        
        # Таймер для автоматического обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(10000)  # Обновляем каждые 10 секунд

    def set_operation_mode(self, in_progress=True):
        """Set operation mode to disable/enable buttons during operations"""
        self.is_operation_in_progress = in_progress
        self.install_btn.setEnabled(not in_progress)
        self.uninstall_btn.setEnabled(not in_progress)
        self.start_btn.setEnabled(not in_progress)
        self.stop_btn.setEnabled(not in_progress)
        self.status_btn.setEnabled(not in_progress)
        self.refresh_btn.setEnabled(not in_progress)
        self.file_combo.setEnabled(not in_progress)

    def _find_bat_files(self):
        """Находит все .bat файлы в корневой директории."""
        try:
            bat_files = self.file_manager.get_bat_files()
            return [os.path.basename(f) for f in bat_files if f.endswith('.bat')]
        except Exception as e:
            print(f"Ошибка поиска .bat файлов: {e}")
            return []

    def _run_worker(self, action):
        """Запускает worker в отдельном потоке."""
        if self.is_operation_in_progress:
            return
            
        selected_file = self.file_combo.currentText()
        if not selected_file:
            QMessageBox.warning(self, "Предупреждение", "Выберите .bat файл")
            return

        bat_file_path = os.path.join(self.file_manager.base_dir, selected_file)
        if not os.path.exists(bat_file_path):
            QMessageBox.critical(self, "Ошибка", f"Файл {selected_file} не найден")
            return

        self.set_operation_mode(True)
        
        # Создаем worker и поток
        self.worker = ServiceWorker("zapret", bat_file_path, action)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)
        
        # Подключаем сигналы
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.error.connect(self.on_worker_error)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.error.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.finished.connect(lambda: self.set_operation_mode(False))
        
        # Запускаем поток
        self.worker_thread.start()

    def on_worker_finished(self, message):
        """Обрабатывает успешное завершение операции."""
        QMessageBox.information(self, "Успех", message)
        self.update_status()
        self.update_buttons_state()

    def on_worker_error(self, message):
        """Обрабатывает ошибку в операции."""
        QMessageBox.critical(self, "Ошибка", message)
        self.update_status()
        self.update_buttons_state()

    def update_buttons_state(self):
        """Обновляет состояние кнопок в зависимости от статуса службы."""
        try:
            status = self.check_service_status()
            service_running = "работает" in status.lower() or "running" in status.lower()
            service_exists = "не установлена" not in status.lower()
            
            self.install_btn.setEnabled(not service_exists and not self.is_operation_in_progress)
            self.uninstall_btn.setEnabled(service_exists and not self.is_operation_in_progress)
            self.start_btn.setEnabled(service_exists and not service_running and not self.is_operation_in_progress)
            self.stop_btn.setEnabled(service_exists and service_running and not self.is_operation_in_progress)
            self.status_btn.setEnabled(not self.is_operation_in_progress)
            self.refresh_btn.setEnabled(not self.is_operation_in_progress)
            
        except Exception as e:
            print(f"Ошибка обновления состояния кнопок: {e}")

    def install_service(self):
        """Устанавливает службу."""
        self._run_worker("install")

    def remove_service(self):
        """Удаляет службу."""
        reply = QMessageBox.question(self, "Подтверждение", 
                                   "Вы уверены, что хотите удалить службу?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._run_worker("remove")

    def start_service(self):
        """Запускает службу."""
        self._run_worker("start")

    def stop_service(self):
        """Останавливает службу."""
        self._run_worker("stop")

    def update_service_status(self):
        """Обновляет отображение статуса службы."""
        try:
            status = self.check_service_status()
            
            if "работает" in status.lower() or "running" in status.lower():
                self.status_label.setText(f"Статус: {status}")
                self.status_label.setStyleSheet(self.get_label_style("success"))
            elif "остановлена" in status.lower() or "stopped" in status.lower():
                self.status_label.setText(f"Статус: {status}")
                self.status_label.setStyleSheet(self.get_label_style("warning"))
            elif "не установлена" in status.lower():
                self.status_label.setText(f"Статус: {status}")
                self.status_label.setStyleSheet(self.get_label_style("error"))
            else:
                self.status_label.setText(f"Статус: {status}")
                self.status_label.setStyleSheet(self.get_label_style("info"))
                
        except Exception as e:
            print(f"Ошибка обновления статуса службы: {e}")
            self.status_label.setText("Статус: Ошибка проверки")
            self.status_label.setStyleSheet(self.get_label_style("error"))

    def check_service_status(self):
        """Проверяет статус службы Windows."""
        try:
            # Проверяем службу 'zapret'
            result = subprocess.run(
                ['sc', 'query', 'zapret'], 
                capture_output=True, 
                text=True, 
                encoding='cp866'
            )
            
            if result.returncode == 0:
                # Служба найдена, парсим её статус
                for line in result.stdout.split('\n'):
                    if 'STATE' in line.upper():
                        if 'RUNNING' in line.upper():
                            return "Работает (служба zapret)"
                        elif 'STOPPED' in line.upper():
                            return "Остановлена (служба zapret)"
                        elif 'STARTING' in line.upper():
                            return "Запускается (служба zapret)"
                        elif 'STOPPING' in line.upper():
                            return "Останавливается (служба zapret)"
                        else:
                            return f"Неизвестно (служба zapret)"
            
            # Если служба не найдена, проверяем процесс winws.exe
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq winws.exe'], 
                capture_output=True, 
                text=True, 
                encoding='cp866'
            )
            
            if result.returncode == 0 and 'winws.exe' in result.stdout:
                return "Работает (процесс winws.exe)"
            
            # Если ни служба, ни процесс не найдены
            return "Служба не установлена"
            
        except Exception as e:
            return f"Ошибка: {str(e)}"

    def check_status(self):
        """Проверяет статус службы."""
        self.update_service_status()

    def refresh_profiles(self):
        """Обновляет список доступных .bat файлов."""
        try:
            bat_files = self._find_bat_files()
            self.file_combo.clear()
            if bat_files:
                self.file_combo.addItems(bat_files)
                self.file_combo.setCurrentIndex(0)
                self.update_service_info()
            else:
                self.service_info.setText("Не найдено .bat файлов")
        except Exception as e:
            print(f"Ошибка обновления профилей: {e}")
            self.service_info.setText("Ошибка загрузки профилей")

    def update_status(self):
        """Обновляет статус службы."""
        if not self.is_operation_in_progress:
            self.update_service_status()
            self.update_buttons_state()

    def update_service_info(self):
        """Обновляет информацию о выбранной службе."""
        try:
            selected_file = self.file_combo.currentText()
            if not selected_file:
                self.service_info.setText("Выберите файл для отображения информации о службе")
                return

            bat_file_path = os.path.join(self.file_manager.base_dir, selected_file)
            if not os.path.exists(bat_file_path):
                self.service_info.setText(f"Файл {selected_file} не найден")
                return

            # Читаем содержимое .bat файла
            with open(bat_file_path, 'r', encoding='cp866') as f:
                content = f.read()

            # Извлекаем полезную информацию
            info_lines = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('@') and not line.startswith('REM'):
                    if 'winws.exe' in line:
                        # Показываем аргументы winws.exe
                        args = line.split('winws.exe')[-1].strip()
                        if args:
                            info_lines.append(f"Аргументы: {args}")
                    elif 'echo' in line.lower():
                        # Показываем echo сообщения
                        echo_msg = line.split('echo')[-1].strip()
                        if echo_msg:
                            info_lines.append(f"Сообщение: {echo_msg}")

            if info_lines:
                info_text = f"Файл: {selected_file}\n\n" + "\n".join(info_lines)
            else:
                info_text = f"Файл: {selected_file}\n\nСодержимое файла не содержит полезной информации для отображения."

            self.service_info.setText(info_text)
            
        except Exception as e:
            print(f"Ошибка обновления информации о службе: {e}")
            self.service_info.setText(f"Ошибка чтения файла: {str(e)}")

    def stop_threads(self):
        """Останавливает все потоки при закрытии."""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        if self.status_timer:
            self.status_timer.stop()
