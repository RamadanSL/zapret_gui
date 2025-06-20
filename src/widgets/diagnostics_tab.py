import socket
import subprocess
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QTextEdit, 
                               QGroupBox, QSizePolicy)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont, QColor

from utils.process_manager import ServiceManager

class DiagnosticsWorker(QThread):
    """Выполняет диагностику в фоновом потоке."""
    progress = Signal(str)
    finished = Signal()

    def __init__(self, service_manager):
        super().__init__()
        self.service_manager = service_manager

    def run(self):
        self.progress.emit("--- Начало диагностики ---")

        # 1. Проверка прав администратора
        self.progress.emit("\n[1/4] Проверка прав доступа...")
        if self.service_manager.is_admin():
            self.progress.emit("    <font color='green'>OK:</font> Приложение запущено с правами администратора.")
        else:
            self.progress.emit("    <font color='orange'>ВНИМАНИЕ:</font> Приложение запущено без прав администратора. Некоторые проверки могут быть недоступны.")

        # 2. Проверка статуса служб
        self.progress.emit("\n[2/4] Проверка статуса служб...")
        zapret_status = self.service_manager.get_service_status()
        if zapret_status == 'RUNNING':
            self.progress.emit("    <font color='green'>OK:</font> Служба 'zapret' запущена.")
        elif zapret_status == 'STOPPED':
            self.progress.emit("    <font color='orange'>ВНИМАНИЕ:</font> Служба 'zapret' установлена, но не запущена.")
        else:
            self.progress.emit("    <font color='red'>ОШИБКА:</font> Служба 'zapret' не найдена.")
        
        # Проверка WinDivert (аналогично)
        windivert_manager = ServiceManager(service_name="WinDivert")
        windivert_status = windivert_manager.get_service_status()
        if windivert_status == 'RUNNING':
            self.progress.emit("    <font color='green'>OK:</font> Служба 'WinDivert' запущена.")
        else:
            self.progress.emit("    <font color='orange'>ВНИМАНИЕ:</font> Служба 'WinDivert' не найдена или не запущена.")

        # 3. Проверка сетевых портов
        self.progress.emit("\n[3/4] Проверка сетевых портов...")
        ports_to_check = [53, 12345] # Пример портов (DNS, baddr)
        for port in ports_to_check:
            if self.is_port_in_use(port):
                self.progress.emit(f"    <font color='orange'>ВНИМАНИЕ:</font> Порт {port} уже используется. Возможны конфликты.")
            else:
                self.progress.emit(f"    <font color='green'>OK:</font> Порт {port} свободен.")

        # 4. Проверка доступа к сети
        self.progress.emit("\n[4/4] Проверка доступа к сети...")
        if self.check_internet_connection():
            self.progress.emit("    <font color='green'>OK:</font> Доступ в Интернет есть.")
        else:
             self.progress.emit("    <font color='red'>ОШИБКА:</font> Нет доступа в Интернет.")

        self.progress.emit("\n--- Диагностика завершена ---")
        self.finished.emit()

    def is_port_in_use(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
            
    def check_internet_connection(self, host="8.8.8.8", port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except socket.error:
            return False


class DiagnosticsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service_manager = ServiceManager()
        self.worker = None

        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Control Group ---
        control_group = QGroupBox("Запуск диагностики")
        control_layout = QVBoxLayout(control_group)

        self.run_button = QPushButton("Начать полную диагностику")
        self.run_button.setFont(QFont("Segoe UI", 12))
        self.run_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.run_button.clicked.connect(self.run_diagnostics)
        control_layout.addWidget(self.run_button)

        main_layout.addWidget(control_group)

        # --- Output Group ---
        output_group = QGroupBox("Результаты диагностики")
        output_layout = QVBoxLayout(output_group)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setStyleSheet("background-color: #f0f0f0;")
        output_layout.addWidget(self.output_text)
        main_layout.addWidget(output_group)

    def run_diagnostics(self):
        self.run_button.setEnabled(False)
        self.run_button.setText("Диагностика выполняется...")
        self.output_text.clear()

        self.worker = DiagnosticsWorker(self.service_manager)
        self.worker.progress.connect(self.output_text.append)
        self.worker.finished.connect(self.on_diagnostics_finished)
        self.worker.start()

    def on_diagnostics_finished(self):
        self.run_button.setEnabled(True)
        self.run_button.setText("Начать полную диагностику")
        self.worker = None 