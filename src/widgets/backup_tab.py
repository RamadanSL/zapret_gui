from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                               QMessageBox, QGroupBox, QFrame, QProgressBar, QSpacerItem, QSizePolicy)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QObject
from PySide6.QtGui import QFont, QIcon
from pathlib import Path
from utils.file_manager import FileManager
from utils.style_utils import StyleUtils

class BackupWorker(QObject):
    """Worker for backup operations"""
    finished = Signal(bool, str)
    
    def __init__(self, operation, file_manager, file_path, backup_suffix):
        super().__init__()
        self.operation = operation
        self.file_manager = file_manager
        self.file_path = file_path
        self.backup_suffix = backup_suffix
        
    def run(self):
        try:
            if self.operation == "backup":
                success = self.file_manager.backup_file(str(self.file_path), self.backup_suffix)
                message = "Резервная копия создана успешно" if success else "Не удалось создать резервную копию"
            else:  # restore
                backup_path = self.file_path.with_suffix(self.file_path.suffix + self.backup_suffix)
                success = self.file_manager.restore_file(str(backup_path))
                message = "Восстановление завершено успешно" if success else "Не удалось восстановить файл"
            
            self.finished.emit(success, message)
        except Exception as e:
            self.finished.emit(False, f"Ошибка: {str(e)}")

class BackupTab(QWidget):
    def __init__(self, file_manager, config_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.config_manager = config_manager
        self.main_window = main_window
        self.backup_suffix = ".bak"
        self.target_file = "ipset-all.txt"
        self.is_operation_running = False
        
        self.init_ui()
        self.update_info()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title_label = QLabel("Резервное копирование")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Info Card
        self.info_card = self.create_info_card()
        layout.addWidget(self.info_card)
        
        # Actions Card
        self.actions_card = self.create_actions_card()
        layout.addWidget(self.actions_card)
        
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
        
    def create_info_card(self):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(StyleUtils.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Информация о файле")
        header_label.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        layout.addWidget(header_label)
        
        # File info
        self.file_info_label = QLabel()
        self.file_info_label.setWordWrap(True)
        self.file_info_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 12px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        layout.addWidget(self.file_info_label)
        
        return card
        
    def create_actions_card(self):
        card = QFrame()
        card.setFrameStyle(QFrame.Shape.StyledPanel)
        card.setStyleSheet(StyleUtils.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("Действия")
        header_label.setFont(QFont("Segoe UI", 14, QFont.Weight.DemiBold))
        layout.addWidget(header_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        self.backup_btn = QPushButton("Создать резервную копию")
        self.backup_btn.setStyleSheet(StyleUtils.get_button_style_material("success"))
        self.backup_btn.clicked.connect(self.create_backup)
        
        self.restore_btn = QPushButton("Восстановить из резервной копии")
        self.restore_btn.setStyleSheet(StyleUtils.get_button_style_material("secondary"))
        self.restore_btn.clicked.connect(self.restore_backup)
        
        btn_layout.addWidget(self.backup_btn)
        btn_layout.addWidget(self.restore_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return card
        
    def update_info(self):
        """Обновляет информацию о наличии бэкапа"""
        file_path = self.file_manager.lists_dir / self.target_file
        backup_path = file_path.with_suffix(file_path.suffix + self.backup_suffix)
        
        info = f"<b>Файл:</b> {file_path.name}<br>"
        info += f"<b>Путь:</b> {file_path}<br><br>"
        
        if backup_path.exists():
            backup_size = backup_path.stat().st_size
            backup_size_mb = backup_size / (1024 * 1024)
            info += f"<b>Резервная копия:</b> {backup_path.name}<br>"
            info += f"<b>Размер:</b> {backup_size_mb:.2f} МБ<br>"
            info += f"<b>Статус:</b> <span style='color: #4caf50;'>✓ Доступна</span>"
            self.restore_btn.setEnabled(True)
            self.restore_btn.setStyleSheet(StyleUtils.get_button_style_material("secondary"))
        else:
            info += f"<b>Резервная копия:</b> отсутствует<br>"
            info += f"<b>Статус:</b> <span style='color: #f44336;'>✗ Не найдена</span>"
            self.restore_btn.setEnabled(False)
            self.restore_btn.setStyleSheet(StyleUtils.get_button_style_material("secondary"))
            
        self.file_info_label.setText(info)
        
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
        
    def set_operation_running(self, running):
        """Устанавливает состояние операции"""
        self.is_operation_running = running
        self.backup_btn.setEnabled(not running)
        self.restore_btn.setEnabled(not running and self.restore_btn.isEnabled())
        self.progress_bar.setVisible(running)
        
        if running:
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
        
    def create_backup(self):
        if self.is_operation_running:
            return
            
        file_path = self.file_manager.lists_dir / self.target_file
        if not file_path.exists():
            QMessageBox.warning(self, "Ошибка", f"Файл {self.target_file} не найден")
            return
            
        self.set_operation_running(True)
        self.show_status("Создание резервной копии...")
        
        # Run in thread
        self.worker_thread = QThread()
        self.worker = BackupWorker("backup", self.file_manager, file_path, self.backup_suffix)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_backup_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        self.worker_thread.start()
        
    def restore_backup(self):
        if self.is_operation_running:
            return
            
        file_path = self.file_manager.lists_dir / self.target_file
        backup_path = file_path.with_suffix(file_path.suffix + self.backup_suffix)
        
        if not backup_path.exists():
            QMessageBox.warning(self, "Ошибка", "Резервная копия не найдена")
            return
            
        # Confirm restoration
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите восстановить файл из резервной копии?\nТекущий файл будет перезаписан.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        self.set_operation_running(True)
        self.show_status("Восстановление файла...")
        
        # Run in thread
        self.worker_thread = QThread()
        self.worker = BackupWorker("restore", self.file_manager, file_path, self.backup_suffix)
        self.worker.moveToThread(self.worker_thread)
        
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_backup_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        
        self.worker_thread.start()
        
    def on_backup_finished(self, success, message):
        self.set_operation_running(False)
        
        if success:
            self.show_status(message, is_error=False)
            QMessageBox.information(self, "Успех", message)
        else:
            self.show_status(message, is_error=True)
            QMessageBox.critical(self, "Ошибка", message)
            
        self.update_info() 