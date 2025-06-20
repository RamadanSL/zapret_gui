import os
import shutil
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit, QMessageBox, 
                               QHBoxLayout, QGroupBox, QMenu, QMenuBar, QToolButton, 
                               QProgressBar, QLabel, QSplitter, QFrame)
from PySide6.QtCore import QThread, Signal, QObject, Qt, QTimer
from PySide6.QtGui import QColor, QTextCursor, QFontDatabase, QFont, QAction, QIcon

from utils.style_utils import StyleUtils

class DiagnosticsWorker(QObject):
    """
    Выполняет диагностические задачи в фоновом потоке.
    """
    result = Signal(str, QColor)
    error = Signal(str)
    finished = Signal()
    progress = Signal(int)

    def __init__(self, task='all', parent=None):
        super().__init__(parent)
        self.task = task
        self._is_running = True

    def run(self):
        """Запускает выполнение задач с обработкой ошибок."""
        try:
            tasks_to_run = []
            if self.task == 'all':
                tasks_to_run = [self.check_conflicts, self.check_dns, self.check_network, self.check_services]
                self.progress.emit(0)
            elif self.task == 'conflicts':
                tasks_to_run = [self.check_conflicts]
                self.progress.emit(0)
            elif self.task == 'dns':
                tasks_to_run = [self.check_dns]
                self.progress.emit(0)
            elif self.task == 'network':
                tasks_to_run = [self.check_network]
                self.progress.emit(0)
            elif self.task == 'services':
                tasks_to_run = [self.check_services]
                self.progress.emit(0)

            total_tasks = len(tasks_to_run)
            for i, task_func in enumerate(tasks_to_run):
                if not self._is_running:
                    break
                task_func()
                progress = int((i + 1) / total_tasks * 100)
                self.progress.emit(progress)
        except Exception as e:
            import traceback
            error_info = f"Критическая ошибка в потоке диагностики:\n{traceback.format_exc()}"
            self.error.emit(error_info)
        finally:
            if self._is_running:
                self.finished.emit()
    
    def stop(self):
        """Останавливает выполнение."""
        self._is_running = False

    def _run_command(self, command):
        """Безопасно выполняет системную команду."""
        return subprocess.run(
            command,
            capture_output=True, text=True, encoding='cp866',
            errors='ignore', # Игнорируем ошибки кодировки
            creationflags=subprocess.CREATE_NO_WINDOW
        )

    def check_conflicts(self):
        """Проверяет конфликтующие процессы."""
        if not self._is_running: return
        self.result.emit("🔍 Проверка конфликтующих процессов\n", QColor("#1976d2"))
        self.result.emit("=" * 50 + "\n", QColor("#666666"))
        
        conflict_processes = [
            'goodbyedpi.exe', 'PowerTunnel.exe', 'simplewall.exe', 
            'glasswire.exe', 'comodo.exe', 'avast.exe', 'avg.exe'
        ]
        
        for i, process in enumerate(conflict_processes):
            if not self._is_running: return
            try:
                res = self._run_command(['tasklist', '/FI', f'IMAGENAME eq {process}'])
                if process.lower() in res.stdout.lower():
                    self.result.emit(f"⚠️  Обнаружен конфликтующий процесс: {process}\n", QColor("#ff9800"))
                else:
                    self.result.emit(f"✅ Конфликтующий процесс {process} не найден\n", QColor("#4caf50"))
            except Exception as e:
                self.result.emit(f"❌ Ошибка при проверке процесса {process}: {e}\n", QColor("#f44336"))

    def check_dns(self):
        """Проверяет DNS-серверы."""
        if not self._is_running: return
        self.result.emit("\n🌐 Проверка DNS-серверов\n", QColor("#1976d2"))
        self.result.emit("=" * 50 + "\n", QColor("#666666"))
        
        try:
            res = self._run_command(['ipconfig', '/all'])
            dns_found = False
            for line in res.stdout.split('\n'):
                if not self._is_running: return
                if 'dns-серверы' in line.lower() or 'dns servers' in line.lower():
                    dns_ip = line.split(':')[-1].strip()
                    if '127.0.0.1' in dns_ip:
                        self.result.emit(f"✅ Обнаружен корректный локальный DNS-сервер: {dns_ip}\n", QColor("#4caf50"))
                        dns_found = True
                        break 
            if not dns_found:
                self.result.emit("⚠️  Локальный DNS-сервер (127.0.0.1) не найден. Служба может работать некорректно.\n", QColor("#ff9800"))
        except Exception as e:
            self.result.emit(f"❌ Ошибка при проверке DNS: {e}\n", QColor("#f44336"))

    def check_network(self):
        """Проверяет сетевые настройки."""
        if not self._is_running: return
        self.result.emit("\n🌍 Проверка сетевых настроек\n", QColor("#1976d2"))
        self.result.emit("=" * 50 + "\n", QColor("#666666"))
        
        try:
            # Проверяем доступность интернета
            res = self._run_command(['ping', '-n', '1', '8.8.8.8'])
            if res.returncode == 0:
                self.result.emit("✅ Интернет-соединение активно\n", QColor("#4caf50"))
            else:
                self.result.emit("⚠️  Проблемы с интернет-соединением\n", QColor("#ff9800"))
                
            # Проверяем локальный хост
            res = self._run_command(['ping', '-n', '1', '127.0.0.1'])
            if res.returncode == 0:
                self.result.emit("✅ Локальный хост доступен\n", QColor("#4caf50"))
            else:
                self.result.emit("❌ Проблемы с локальным хостом\n", QColor("#f44336"))
                
        except Exception as e:
            self.result.emit(f"❌ Ошибка при проверке сети: {e}\n", QColor("#f44336"))

    def check_services(self):
        """Проверяет службы Windows."""
        if not self._is_running: return
        self.result.emit("\n⚙️ Проверка служб Windows\n", QColor("#1976d2"))
        self.result.emit("=" * 50 + "\n", QColor("#666666"))
        
        services_to_check = ['zapret', 'WinDivert', 'WinDivert14']
        
        for service in services_to_check:
            if not self._is_running: return
            try:
                res = self._run_command(['sc', 'query', service])
                if res.returncode == 0:
                    if 'RUNNING' in res.stdout.upper():
                        self.result.emit(f"✅ Служба {service} запущена\n", QColor("#4caf50"))
                    elif 'STOPPED' in res.stdout.upper():
                        self.result.emit(f"⚠️  Служба {service} остановлена\n", QColor("#ff9800"))
                    else:
                        self.result.emit(f"ℹ️  Служба {service} найдена\n", QColor("#2196f3"))
                else:
                    self.result.emit(f"ℹ️  Служба {service} не установлена\n", QColor("#9e9e9e"))
            except Exception as e:
                self.result.emit(f"❌ Ошибка при проверке службы {service}: {e}\n", QColor("#f44336"))


class DiagnosticsTab(QWidget):
    """Вкладка для диагностики проблем с современным дизайном."""
    
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.worker = None
        self.worker_thread = None
        self.is_operation_in_progress = False
        self.init_ui()

    def init_ui(self):
        """Инициализирует пользовательский интерфейс вкладки."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Заголовок
        title_label = QLabel("🔧 Диагностика системы")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1c1b1f;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Создаем сплиттер для лучшей организации
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Верхняя панель с кнопками
        top_panel = self.create_top_panel()
        splitter.addWidget(top_panel)
        
        # Нижняя панель с выводом
        bottom_panel = self.create_bottom_panel()
        splitter.addWidget(bottom_panel)
        
        # Устанавливаем соотношение размеров
        splitter.setSizes([150, 400])
        main_layout.addWidget(splitter)
        
        # Подключаем сигналы
        self.connect_signals()

    def create_top_panel(self):
        """Создает верхнюю панель с кнопками и меню."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e1e1e1;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Группа быстрых действий
        quick_group = QGroupBox("🚀 Быстрые действия")
        quick_group.setStyleSheet(StyleUtils.get_group_style())
        quick_layout = QHBoxLayout(quick_group)
        
        # Кнопка полной диагностики
        self.full_diagnostic_btn = QPushButton("🔍 Полная диагностика")
        self.full_diagnostic_btn.setStyleSheet(StyleUtils.get_button_style("primary"))
        self.full_diagnostic_btn.setMinimumHeight(45)
        self.full_diagnostic_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        quick_layout.addWidget(self.full_diagnostic_btn)
        quick_layout.addStretch()
        
        # Группа специализированных проверок
        specific_group = QGroupBox("🎯 Специализированные проверки")
        specific_group.setStyleSheet(StyleUtils.get_group_style())
        specific_layout = QHBoxLayout(specific_group)
        
        # Создаем выпадающее меню для диагностики
        self.diagnostic_menu_btn = QToolButton()
        self.diagnostic_menu_btn.setText("🔧 Диагностика")
        self.diagnostic_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.diagnostic_menu_btn.setStyleSheet("""
            QToolButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 20px;
                font-weight: bold;
                font-size: 11pt;
                min-height: 40px;
            }
            QToolButton:hover {
                background-color: #1565c0;
            }
            QToolButton:pressed {
                background-color: #0d47a1;
            }
        """)
        
        # Создаем меню
        self.diagnostic_menu = QMenu()
        self.diagnostic_menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #e1e1e1;
                border-radius: 6px;
                padding: 5px;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)
        
        # Добавляем действия в меню
        actions = [
            ("🔍 Проверить конфликты", "conflicts"),
            ("🌐 Проверить DNS", "dns"),
            ("🌍 Проверить сеть", "network"),
            ("⚙️ Проверить службы", "services")
        ]
        
        for text, action in actions:
            menu_action = QAction(text, self)
            menu_action.triggered.connect(lambda checked, a=action: self.run_specific_diagnostic(a))
            self.diagnostic_menu.addAction(menu_action)
        
        self.diagnostic_menu_btn.setMenu(self.diagnostic_menu)
        specific_layout.addWidget(self.diagnostic_menu_btn)
        
        # Кнопка очистки кэша Discord
        self.clean_discord_btn = QPushButton("🧹 Очистить кэш Discord")
        self.clean_discord_btn.setStyleSheet(StyleUtils.get_button_style("warning"))
        self.clean_discord_btn.setMinimumHeight(40)
        self.clean_discord_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        specific_layout.addWidget(self.clean_discord_btn)
        specific_layout.addStretch()
        
        # Прогресс бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(StyleUtils.get_progress_bar_style())
        self.progress_bar.setMinimumHeight(8)
        
        # Добавляем все в layout
        layout.addWidget(quick_group)
        layout.addWidget(specific_group)
        layout.addWidget(self.progress_bar)
        
        return panel

    def create_bottom_panel(self):
        """Создает нижнюю панель с выводом результатов."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e1e1e1;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Заголовок области вывода
        output_header = QLabel("📋 Результаты диагностики")
        output_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1c1b1f;
                padding: 5px 0;
            }
        """)
        layout.addWidget(output_header)
        
        # Область вывода результатов
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11pt;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.output_text)
        
        return panel

    def connect_signals(self):
        """Подключает сигналы кнопок."""
        self.full_diagnostic_btn.clicked.connect(self.run_diagnostics)
        self.clean_discord_btn.clicked.connect(self.clear_discord_cache)

    def set_operation_mode(self, in_progress=True):
        """Устанавливает режим операции."""
        self.is_operation_in_progress = in_progress
        self.full_diagnostic_btn.setEnabled(not in_progress)
        self.diagnostic_menu_btn.setEnabled(not in_progress)
        self.clean_discord_btn.setEnabled(not in_progress)
        
        if in_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
        else:
            self.progress_bar.setVisible(False)

    def run_diagnostics(self):
        """Запускает полную диагностику."""
        self.output_text.clear()
        self.output_text.append("🚀 Запуск полной диагностики системы...\n")
        self.run_specific_diagnostic("all")
        
    def run_specific_diagnostic(self, task):
        """Запускает определенную диагностику в фоновом потоке."""
        if self.is_operation_in_progress:
            return
            
        if task == "all":
            self.output_text.clear()
            self.output_text.append("🚀 Запуск полной диагностики системы...\n")

        self.set_operation_mode(True)

        self.worker_thread = QThread()
        self.worker = DiagnosticsWorker(task)
        self.worker.moveToThread(self.worker_thread)

        self.worker.result.connect(self.append_result)
        self.worker.error.connect(self.on_diagnostics_error)
        self.worker.finished.connect(self.on_diagnostics_finished)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker_thread.started.connect(self.worker.run)

        # Обеспечиваем очистку
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(lambda: self.set_operation_mode(False))

        if self.main_window:
            self.main_window.register_thread(self.worker_thread)

        self.worker_thread.start()

    def append_result(self, text, color):
        """Добавляет текст с заданным цветом в область вывода."""
        self.output_text.setTextColor(color)
        self.output_text.insertPlainText(text)
        self.output_text.moveCursor(QTextCursor.MoveOperation.End)

    def on_diagnostics_error(self, error_message):
        """Обрабатывает критическую ошибку в воркере."""
        self.append_result(f"\n❌ {error_message}\n", QColor("#f44336"))
        self.on_diagnostics_finished()

    def on_diagnostics_finished(self):
        """Обработчик завершения диагностики."""
        if self.worker is not None:
            self.output_text.setTextColor(QColor("#666666"))
            self.output_text.append("\n✅ Диагностика завершена.\n")
            self.worker_thread = None
            self.worker = None
        
    def stop_threads(self):
        """Останавливает фоновые процессы."""
        if hasattr(self, 'worker') and self.worker:
            self.worker.stop()
        if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait(2000)

    def clear_discord_cache(self):
        """Очищает кэш Discord."""
        reply = QMessageBox.question(
            self, 
            '🧹 Очистка кэша Discord', 
            "Это закроет Discord, если он запущен. Вы уверены?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.output_text.clear()
            self.output_text.append("🧹 Очистка кэша Discord...\n")
            
            # Запускаем очистку в отдельном потоке
            self.clean_discord_btn.setEnabled(False)
            self.clear_cache_thread = QThread()
            self.clear_cache_worker = ClearCacheWorker()
            self.clear_cache_worker.moveToThread(self.clear_cache_thread)

            self.clear_cache_worker.result.connect(lambda text: self.append_result(text, QColor("#333333")))
            self.clear_cache_worker.finished.connect(lambda: (
                self.append_result("\n✅ Очистка завершена.\n", QColor("#4caf50")),
                self.clean_discord_btn.setEnabled(True),
                self.clear_cache_thread.quit()
            ))

            self.clear_cache_thread.started.connect(self.clear_cache_worker.run)
            self.clear_cache_thread.finished.connect(self.clear_cache_thread.deleteLater)
            self.clear_cache_worker.finished.connect(self.clear_cache_worker.deleteLater)

            if self.main_window:
                self.main_window.register_thread(self.clear_cache_thread)

            self.clear_cache_thread.start()


class ClearCacheWorker(QObject):
    """Воркер для очистки кэша в фоновом потоке."""
    result = Signal(str)
    finished = Signal()

    def run(self):
        """Выполняет очистку."""
        try:
            self.result.emit("🔄 Попытка закрыть Discord...\n")
            subprocess.run('taskkill /F /IM Discord.exe', capture_output=True, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            self.result.emit("✅ Процесс Discord завершен (если был запущен).\n")

            appdata_path = os.getenv('APPDATA')
            if not appdata_path:
                self.result.emit("❌ Ошибка: не удалось найти папку AppData.\n")
                self.finished.emit()
                return

            discord_cache_path = os.path.join(appdata_path, 'discord', 'Cache')
            if os.path.exists(discord_cache_path):
                try:
                    shutil.rmtree(discord_cache_path)
                    self.result.emit(f"✅ Папка кэша Discord успешно удалена.\n")
                except Exception as e:
                    self.result.emit(f"❌ Не удалось удалить кэш Discord: {e}\n")
            else:
                self.result.emit(f"ℹ️  Папка кэша Discord не найдена.\n")

        except Exception as e:
            self.result.emit(f"❌ Произошла ошибка при очистке: {e}\n")
        finally:
            self.finished.emit() 