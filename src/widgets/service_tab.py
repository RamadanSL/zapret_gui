import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                               QMessageBox, QGroupBox, QFileDialog, QSizePolicy,
                               QGridLayout)
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtGui import QFont

from utils.process_manager import ServiceManager

# Worker thread for service operations
class ServiceWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, action, service_manager, data=None):
        super().__init__()
        self.action = action
        self.service_manager = service_manager
        self.data = data # Может быть bat_file или start_type

    def run(self):
        result, message = False, "Unknown action"
        actions = {
            "install": lambda: self.service_manager.install_service(self.data),
            "uninstall": lambda: self.service_manager.uninstall_service(),
            "start": lambda: self.service_manager.start_service(),
            "stop": lambda: self.service_manager.stop_service(),
            "restart": lambda: self.service_manager.restart_service(),
            "set_auto": lambda: self.service_manager.set_service_start_type("auto"),
            "set_demand": lambda: self.service_manager.set_service_start_type("demand"),
            "start_manual": lambda: self.service_manager.start_manual_process(self.data),
            "stop_manual": lambda: self.service_manager.stop_manual_process()
        }
        if self.action in actions:
            result, message = actions[self.action]()
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
        self.status_timer.timeout.connect(self.update_ui_states)
        self.status_timer.start(3000)  # Check every 3 seconds
        self.update_ui_states()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- ОБЩИЙ СТАТУС ---
        status_box = QGroupBox("Общий статус")
        status_layout = QHBoxLayout(status_box)
        self.overall_status_label = QLabel("Проверка...")
        font = self.overall_status_label.font(); font.setPointSize(14); font.setBold(True)
        self.overall_status_label.setFont(font)
        status_layout.addWidget(self.overall_status_label)
        main_layout.addWidget(status_box)

        # --- УПРАВЛЕНИЕ СЛУЖБОЙ ---
        service_box = QGroupBox("Управление службой Windows")
        service_grid = QGridLayout(service_box)
        
        self.install_button = QPushButton("Установить")
        self.uninstall_button = QPushButton("Удалить")
        self.start_button = QPushButton("Запустить")
        self.stop_button = QPushButton("Остановить")
        self.restart_button = QPushButton("Перезапустить")

        service_grid.addWidget(self.install_button, 0, 0)
        service_grid.addWidget(self.uninstall_button, 0, 1)
        service_grid.addWidget(self.start_button, 1, 0)
        service_grid.addWidget(self.stop_button, 1, 1)
        service_grid.addWidget(self.restart_button, 1, 2)
        
        # --- Автозапуск ---
        self.autostart_status_label = QLabel("Тип запуска: ?")
        self.autostart_on_button = QPushButton("Вкл. автозапуск")
        self.autostart_off_button = QPushButton("Откл. автозапуск")
        service_grid.addWidget(self.autostart_status_label, 2, 0, 1, 2)
        service_grid.addWidget(self.autostart_on_button, 3, 0)
        service_grid.addWidget(self.autostart_off_button, 3, 1)
        
        main_layout.addWidget(service_box)

        # --- РУЧНОЙ ЗАПУСК ---
        manual_box = QGroupBox("Ручной запуск (для тестов)")
        manual_layout = QVBoxLayout(manual_box)
        self.manual_status_label = QLabel("Статус: неактивен")
        self.manual_start_button = QPushButton("Выбрать .bat и запустить")
        self.manual_stop_button = QPushButton("Остановить ручной запуск")
        manual_layout.addWidget(self.manual_status_label)
        manual_layout.addWidget(self.manual_start_button)
        manual_layout.addWidget(self.manual_stop_button)
        main_layout.addWidget(manual_box)

        main_layout.addStretch()

    def setup_connections(self):
        # Service
        self.install_button.clicked.connect(self.install_service)
        self.uninstall_button.clicked.connect(lambda: self.run_operation("uninstall"))
        self.start_button.clicked.connect(lambda: self.run_operation("start"))
        self.stop_button.clicked.connect(lambda: self.run_operation("stop"))
        self.restart_button.clicked.connect(lambda: self.run_operation("restart"))
        # Autostart
        self.autostart_on_button.clicked.connect(lambda: self.run_operation("set_auto"))
        self.autostart_off_button.clicked.connect(lambda: self.run_operation("set_demand"))
        # Manual
        self.manual_start_button.clicked.connect(self.start_manual)
        self.manual_stop_button.clicked.connect(lambda: self.run_operation("stop_manual"))

    def update_ui_states(self):
        # Получаем все статусы
        service_status = self.service_manager.get_service_status()
        start_type = self.service_manager.get_service_start_type()
        is_manual_running = self.service_manager.is_manual_process_running()
        is_admin = self.service_manager.is_admin()

        # По умолчанию все выключаем
        all_buttons = self.findChildren(QPushButton)
        for btn in all_buttons: btn.setEnabled(False)

        if not is_admin:
            self.overall_status_label.setText("НЕТ ПРАВ АДМИНИСТРАТОРА"); self.overall_status_label.setStyleSheet("color: red;")
            return

        # Логика состояний
        if is_manual_running:
            self.overall_status_label.setText("РУЧНОЙ ЗАПУСК АКТИВЕН"); self.overall_status_label.setStyleSheet("color: blue;")
            self.manual_status_label.setText(f"Активен (PID: {self.service_manager.manual_process_pid})")
            self.manual_stop_button.setEnabled(True)
            # Все остальное блокируется
            return

        self.manual_status_label.setText("Статус: неактивен")
        self.manual_start_button.setEnabled(True)

        # Управление службой
        if service_status == "RUNNING":
            self.overall_status_label.setText("СЛУЖБА ЗАПУЩЕНА"); self.overall_status_label.setStyleSheet("color: green;")
            self.stop_button.setEnabled(True)
            self.restart_button.setEnabled(True)
            self.uninstall_button.setEnabled(True)
            self.autostart_on_button.setEnabled(True)
            self.autostart_off_button.setEnabled(True)
        elif service_status == "STOPPED":
            self.overall_status_label.setText("СЛУЖБА ОСТАНОВЛЕНА"); self.overall_status_label.setStyleSheet("color: orange;")
            self.start_button.setEnabled(True)
            self.install_button.setEnabled(True)
            self.uninstall_button.setEnabled(True)
            self.autostart_on_button.setEnabled(True)
            self.autostart_off_button.setEnabled(True)
        else: # NOT_FOUND
            self.overall_status_label.setText("СЛУЖБА НЕ УСТАНОВЛЕНА"); self.overall_status_label.setStyleSheet("color: red;")
            self.install_button.setEnabled(True)
        
        # Статус автозапуска
        if start_type == "AUTO":
            self.autostart_status_label.setText("Тип запуска: Автоматический")
            self.autostart_on_button.setEnabled(False)
        elif start_type == "DEMAND":
            self.autostart_status_label.setText("Тип запуска: Вручную")
            self.autostart_off_button.setEnabled(False)
        else:
            self.autostart_status_label.setText("Тип запуска: -")

    def install_service(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите .bat файл", "", "Batch Files (*.bat)")
        if path: self.run_operation("install", data=path)

    def start_manual(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите .bat файл", "", "Batch Files (*.bat)")
        if path: self.run_operation("start_manual", data=path)

    def run_operation(self, action, data=None):
        self.worker = ServiceWorker(action, self.service_manager, data)
        self.worker.finished.connect(self.on_operation_finished)
        self.status_timer.stop() # Останавливаем таймер на время операции
        self.worker.start()

    def on_operation_finished(self, success, message):
        if success: QMessageBox.information(self, "Успех", message)
        else: QMessageBox.critical(self, "Ошибка", message)
        self.update_ui_states()
        self.status_timer.start() # Запускаем таймер снова 