import webbrowser
import urllib.request
import urllib.error
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox, 
                               QFrame, QHBoxLayout, QProgressBar, QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal, QObject, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap
from utils.style_utils import StyleUtils

class UpdateCheckWorker(QObject):
    """Проверяет обновления в отдельном потоке."""
    result_ready = Signal(str, str) # new_version, current_version
    finished = Signal()

    def run(self):
        try:
            # Чтение текущей версии
            if not os.path.exists('.version'):
                self.result_ready.emit("error: Файл .version не найден", "")
                return
                
            with open('.version', 'r', encoding='utf-8') as f:
                current_version = f.read().strip()
            
            # Загрузка новой версии
            url = "https://raw.githubusercontent.com/Flowseal/zapret-discord-youtube/master/.version"
            with urllib.request.urlopen(url, timeout=10) as response:
                new_version = response.read().decode('utf-8').strip()
            
            self.result_ready.emit(new_version, current_version)

        except FileNotFoundError:
            self.result_ready.emit("error: Файл .version не найден", "")
        except urllib.error.HTTPError as e:
            self.result_ready.emit(f"error: HTTP ошибка {e.code}: {e.reason}", "")
        except urllib.error.URLError as e:
            self.result_ready.emit(f"error: Ошибка сети: {e}", "")
        except Exception as e:
            self.result_ready.emit(f"error: {e}", "")
        finally:
            self.finished.emit()

class AboutTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_checking_updates = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Title Card
        title_card = self.create_title_card()
        layout.addWidget(title_card)
        
        # Info Card
        info_card = self.create_info_card()
        layout.addWidget(info_card)
        
        # Actions Card
        actions_card = self.create_actions_card()
        layout.addWidget(actions_card)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(StyleUtils.get_progress_bar_style())
        layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet(StyleUtils.get_status_style_material("info"))
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Timer for status clearing
        self.status_timer = QTimer()
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.clear_status)

    def create_title_card(self):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(StyleUtils.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # App title
        title_label = QLabel("Zapret Manager")
        title_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(title_label)
        
        # Version info
        version_label = QLabel("Графический интерфейс для управления zapret")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        layout.addWidget(version_label)
        
        return card
        
    def create_info_card(self):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(StyleUtils.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Информация о проекте")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        layout.addWidget(header_label)
        
        # Project info
        info_text = """
        <div style='background-color: #f8f9fa; border: 1px solid #e9ecef; border-radius: 8px; padding: 15px;'>
            <p><b>Описание:</b> Удобный графический интерфейс для управления системой zapret</p>
            <p><b>Автор:</b> Flowseal</p>
            <p><b>Лицензия:</b> MIT</p>
            <p><b>Язык:</b> Python + PySide6</p>
        </div>
        """
        
        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        layout.addWidget(info_label)
        
        return card
        
    def create_actions_card(self):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(StyleUtils.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Действия")
        header_label.setFont(QFont("Segoe UI", 16, QFont.Weight.DemiBold))
        layout.addWidget(header_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        github_button = QPushButton("Страница проекта на GitHub")
        github_button.setStyleSheet(StyleUtils.get_button_style_material("secondary"))
        github_button.clicked.connect(self.open_github)
        
        self.update_button = QPushButton("Проверить обновления")
        self.update_button.setStyleSheet(StyleUtils.get_button_style_material("info"))
        self.update_button.clicked.connect(self.check_for_updates)
        
        btn_layout.addWidget(github_button)
        btn_layout.addWidget(self.update_button)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return card
        
    def show_status(self, message, is_error=False):
        """Показывает статусное сообщение"""
        self.status_label.setText(message)
        self.status_label.setVisible(True)
        
        if is_error:
            self.status_label.setStyleSheet(StyleUtils.get_status_style_material("error"))
        else:
            self.status_label.setStyleSheet(StyleUtils.get_status_style_material("success"))
            
        self.status_timer.start(5000)  # Clear after 5 seconds
        
    def clear_status(self):
        """Очищает статусное сообщение"""
        self.status_label.setVisible(False)
        
    def set_checking_updates(self, checking):
        """Устанавливает состояние проверки обновлений"""
        self.is_checking_updates = checking
        self.update_button.setEnabled(not checking)
        self.progress_bar.setVisible(checking)
        
        if checking:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
            self.update_button.setText("Проверка...")
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            self.update_button.setText("Проверить обновления")

    def open_github(self):
        webbrowser.open("https://github.com/Flowseal/zapret-discord-youtube")

    def check_for_updates(self):
        if self.is_checking_updates:
            return
            
        self.set_checking_updates(True)
        self.show_status("Проверка обновлений...")

        if hasattr(self, 'worker_thread') and self.worker_thread.isRunning():
             self.set_checking_updates(False)
             return

        self.worker_thread = QThread()
        self.worker = UpdateCheckWorker()
        self.worker.moveToThread(self.worker_thread)

        self.worker_thread.started.connect(self.worker.run)
        self.worker.result_ready.connect(self.on_update_check_finished)
        
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        self.worker_thread.start()

    def on_update_check_finished(self, new_version, current_version):
        self.set_checking_updates(False)

        if new_version.startswith("error:"):
            error_msg = new_version.replace('error: ', '')
            self.show_status(f"Ошибка: {error_msg}", is_error=True)
            QMessageBox.critical(self, "Ошибка", f"Не удалось проверить обновления:\n{error_msg}")
            return

        if new_version == current_version:
            self.show_status("У вас установлена последняя версия", is_error=False)
            QMessageBox.information(self, "Обновления", "У вас установлена последняя версия.")
        else:
            self.show_status(f"Доступна новая версия: {new_version}", is_error=False)
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText(f"Доступна новая версия: {new_version}\n"
                          f"Ваша версия: {current_version}")
            msg_box.setInformativeText("Перейти на страницу загрузки?")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            
            ret = msg_box.exec()
            if ret == QMessageBox.StandardButton.Yes:
                webbrowser.open(f"https://github.com/Flowseal/zapret-discord-youtube/releases/tag/{new_version}") 