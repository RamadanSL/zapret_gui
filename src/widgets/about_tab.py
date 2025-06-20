import webbrowser
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QGroupBox, QHBoxLayout)
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QFont

from utils.update_checker import UpdateChecker

# Определяем текущую версию здесь, чтобы она была в одном месте
APP_VERSION = "1.8.0" 

class UpdateWorker(QThread):
    """Выполняет проверку обновлений в фоновом потоке."""
    result_ready = Signal(bool, str, str) # is_update, message, url

    def run(self):
        checker = UpdateChecker(current_version=APP_VERSION)
        is_available, version, url, error = checker.check_for_updates()
        if error:
            self.result_ready.emit(False, error, None)
        else:
            if is_available:
                message = f"Доступна новая версия: {version}"
                self.result_ready.emit(True, message, url)
            else:
                message = f"У вас установлена последняя версия ({version})."
                self.result_ready.emit(False, message, None)


class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self.release_url = None
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Title ---
        title_label = QLabel("Zapret GUI")
        font = title_label.font()
        font.setPointSize(24)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # --- Version Info ---
        version_label = QLabel(f"Версия: {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #555;")
        main_layout.addWidget(version_label)
        
        main_layout.addSpacing(20)

        # --- Update Group ---
        update_group = QGroupBox("Обновления")
        update_layout = QVBoxLayout(update_group)

        self.update_status_label = QLabel("Нажмите кнопку, чтобы проверить наличие обновлений.")
        self.update_status_label.setWordWrap(True)
        
        self.check_button = QPushButton("Проверить обновления")
        self.check_button.clicked.connect(self.check_for_updates)
        
        self.download_button = QPushButton("Перейти на страницу релиза")
        self.download_button.setVisible(False)
        self.download_button.clicked.connect(self.open_release_page)

        update_layout.addWidget(self.update_status_label)
        update_layout.addWidget(self.check_button)
        update_layout.addWidget(self.download_button)
        main_layout.addWidget(update_group)
        
        main_layout.addStretch()

    def check_for_updates(self):
        self.check_button.setEnabled(False)
        self.check_button.setText("Проверка...")
        self.update_status_label.setText("Подключение к серверу GitHub...")
        self.download_button.setVisible(False)

        self.worker = UpdateWorker()
        self.worker.result_ready.connect(self.on_update_check_finished)
        self.worker.start()

    def on_update_check_finished(self, is_update, message, url):
        self.update_status_label.setText(message)
        self.check_button.setEnabled(True)
        self.check_button.setText("Проверить обновления")
        
        if is_update and url:
            self.release_url = url
            self.download_button.setVisible(True)
            self.update_status_label.setStyleSheet("color: green;")
        elif not is_update and not url: # Error case
             self.update_status_label.setStyleSheet("color: red;")
        else: # Up-to-date case
            self.update_status_label.setStyleSheet("color: blue;")

    def open_release_page(self):
        if self.release_url:
            webbrowser.open(self.release_url) 