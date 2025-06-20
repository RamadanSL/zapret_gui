import os
import requests
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGroupBox, QCheckBox, QSizePolicy, QPushButton,
                               QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from utils.config_manager import ConfigManager

class DownloadWorker(QThread):
    """Скачивает файл в фоновом потоке."""
    progress = Signal(int)
    finished = Signal(bool, str) # success, message

    def __init__(self, url, save_path):
        super().__init__()
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=15)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            progress_percent = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(progress_percent)
            
            self.progress.emit(100)
            self.finished.emit(True, f"Файл успешно скачан и сохранен в {self.save_path}")

        except requests.exceptions.RequestException as e:
            self.finished.emit(False, f"Ошибка сети при скачивании: {e}")
        except Exception as e:
            self.finished.emit(False, f"Произошла ошибка: {e}")


class ListsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()
        self.download_worker = None
        self.ipset_url = "https://raw.githubusercontent.com/zapret-info/z-i/master/ipset-all.txt"
        self.save_path = os.path.abspath("lists/ipset-all.txt")

        self.setup_ui()
        self.update_ipset_status()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- IPset Group ---
        ipset_group = QGroupBox("Режим IPset")
        ipset_layout = QVBoxLayout(ipset_group)
        
        description = QLabel(
            "Включение этого режима активирует использование списков IP-адресов (ipset) для более эффективной фильтрации. "
            "Это может улучшить производительность, но требует соответствующей настройки в конфигурационном файле службы."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #888; padding-bottom: 10px;")
        
        control_layout = QHBoxLayout()
        self.ipset_status_label = QLabel()
        font = self.ipset_status_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.ipset_status_label.setFont(font)

        self.ipset_toggle_switch = QCheckBox()
        self.ipset_toggle_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ipset_toggle_switch.setStyleSheet("""
            QCheckBox::indicator {
                width: 40px;
                height: 20px;
            }
            QCheckBox::indicator:unchecked {
                image: url(src/resources/toggle_off.svg);
            }
            QCheckBox::indicator:checked {
                image: url(src/resources/toggle_on.svg);
            }
        """)
        self.ipset_toggle_switch.toggled.connect(self.toggle_ipset)

        control_layout.addWidget(QLabel("Статус:"))
        control_layout.addWidget(self.ipset_status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.ipset_toggle_switch)
        
        ipset_layout.addWidget(description)
        ipset_layout.addLayout(control_layout)
        main_layout.addWidget(ipset_group)

        # --- IPset Update Group ---
        update_group = QGroupBox("Обновление списков IPset")
        update_layout = QVBoxLayout(update_group)

        self.update_button = QPushButton("Обновить ipset-all.txt с GitHub")
        self.update_button.clicked.connect(self.update_ipset_list)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        update_layout.addWidget(self.update_button)
        update_layout.addWidget(self.progress_bar)
        main_layout.addWidget(update_group)

        main_layout.addStretch()

    def update_ipset_status(self):
        is_enabled = self.config_manager.is_ipset_enabled()
        
        self.ipset_toggle_switch.blockSignals(True)
        self.ipset_toggle_switch.setChecked(is_enabled)
        self.ipset_toggle_switch.blockSignals(False)

        if is_enabled:
            self.ipset_status_label.setText("ВКЛЮЧЕН")
            self.ipset_status_label.setStyleSheet("color: green;")
        else:
            self.ipset_status_label.setText("ВЫКЛЮЧЕН")
            self.ipset_status_label.setStyleSheet("color: red;")

    def toggle_ipset(self, checked):
        if checked:
            self.config_manager.enable_ipset()
        else:
            self.config_manager.disable_ipset()
        self.update_ipset_status()
        
    def update_ipset_list(self):
        self.update_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.download_worker = DownloadWorker(self.ipset_url, self.save_path)
        self.download_worker.progress.connect(self.progress_bar.setValue)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.start()

    def on_download_finished(self, success, message):
        self.update_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(self, "Успех", message)
        else:
            QMessageBox.critical(self, "Ошибка", message) 