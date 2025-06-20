import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QMessageBox, QGroupBox, QFileDialog, QSizePolicy)
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtGui import QFont

from utils.process_manager import ServiceManager

# Worker thread for service operations
class ServiceWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, action, service_manager, bat_file=None):
        super().__init__()
        self.action = action
        self.service_manager = service_manager
        self.bat_file = bat_file

    def run(self):
        result, message = False, "Unknown action"
        if self.action == "install":
            result, message = self.service_manager.install_service(self.bat_file)
        elif self.action == "uninstall":
            result, message = self.service_manager.uninstall_service()
        elif self.action == "start":
            result, message = self.service_manager.start_service()
        elif self.action == "stop":
            result, message = self.service_manager.stop_service()
        elif self.action == "restart":
            result, message = self.service_manager.restart_service()
        self.finished.emit(result, message)


class ServiceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.service_manager = ServiceManager()
        self.worker = None

        # Check for admin rights
        if not self.service_manager.is_admin():
            QMessageBox.warning(self, "Требуются права администратора",
                                "Для управления службами, пожалуйста, перезапустите приложение от имени администратора.")

        self.setup_ui()
        self.setup_connections()

        # Timer to update status
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        self.update_status()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)

        # --- Status Group ---
        status_group = QGroupBox("Статус службы")
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Проверка...")
        font = self.status_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)
        status_layout.addWidget(self.status_label)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # --- Control Group ---
        control_group = QGroupBox("Управление службой")
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.install_button = QPushButton("Установить службу")
        self.uninstall_button = QPushButton("Удалить службу")
        self.start_button = QPushButton("Запустить")
        self.stop_button = QPushButton("Остановить")
        self.restart_button = QPushButton("Перезапустить")
        
        buttons = [self.install_button, self.uninstall_button, self.start_button, self.stop_button, self.restart_button]
        for button in buttons:
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            button.setFont(QFont("Segoe UI", 10))
            control_layout.addWidget(button)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        main_layout.addStretch() # Pushes everything to the top

    def setup_connections(self):
        self.install_button.clicked.connect(self.install_service)
        self.uninstall_button.clicked.connect(lambda: self.run_operation("uninstall"))
        self.start_button.clicked.connect(lambda: self.run_operation("start"))
        self.stop_button.clicked.connect(lambda: self.run_operation("stop"))
        self.restart_button.clicked.connect(lambda: self.run_operation("restart"))

    def update_status(self):
        status = self.service_manager.get_service_status()
        is_admin = self.service_manager.is_admin()
        
        self.set_buttons_enabled(False) # Disable all first

        if not is_admin:
            self.status_label.setText("НЕТ ПРАВ АДМИНИСТРАТОРА")
            self.status_label.setStyleSheet("color: red;")
            return

        if status == "RUNNING":
            self.status_label.setText("СЛУЖБА ЗАПУЩЕНА")
            self.status_label.setStyleSheet("color: green;")
            self.uninstall_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
        elif status == "STOPPED":
            self.status_label.setText("СЛУЖБА ОСТАНОВЛЕНА")
            self.status_label.setStyleSheet("color: orange;")
            self.install_button.setEnabled(True) # Allow re-install/update
            self.uninstall_button.setEnabled(True)
            self.start_button.setEnabled(True)
        else: # NOT_FOUND or UNKNOWN
            self.status_label.setText("СЛУЖБА НЕ УСТАНОВЛЕНА")
            self.status_label.setStyleSheet("color: red;")
            self.install_button.setEnabled(True)
            
    def set_buttons_enabled(self, enabled):
        self.install_button.setEnabled(enabled)
        self.uninstall_button.setEnabled(enabled)
        self.start_button.setEnabled(enabled)
        self.stop_button.setEnabled(enabled)
        self.restart_button.setEnabled(enabled)

    def install_service(self):
        bat_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите .bat файл конфигурации", "", "Batch Files (*.bat)"
        )
        if bat_path:
            self.run_operation("install", bat_file=bat_path)

    def run_operation(self, action, bat_file=None):
        if not self.service_manager.is_admin():
            QMessageBox.critical(self, "Ошибка", "Требуются права администратора для выполнения этой операции.")
            return

        self.set_buttons_enabled(False)
        self.status_label.setText(f"Выполнение: {action.capitalize()}...")
        self.status_label.setStyleSheet("color: blue;")
        
        self.worker = ServiceWorker(action, self.service_manager, bat_file)
        self.worker.finished.connect(self.on_operation_finished)
        self.worker.start()

    def on_operation_finished(self, success, message):
        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", message)
        self.update_status()
        self.worker = None # Clean up worker 