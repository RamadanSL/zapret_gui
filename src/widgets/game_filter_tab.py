from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QMessageBox, QGroupBox, QTextEdit, QComboBox, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QTimer
import os
from pathlib import Path

from utils.process_manager import ProcessManager
from utils.file_manager import FileManager

class GameFilterTab(QWidget):
    """Вкладка для управления игровым фильтром."""
    filter_changed = Signal()

    def __init__(self, file_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.main_window = main_window # Для единообразия
        self.is_operation_in_progress = False
        
        # UI
        self.init_ui()
        
        # Подключаем сигналы
        self.start_btn.clicked.connect(lambda: self.toggle_game_filter(True))
        self.stop_btn.clicked.connect(lambda: self.toggle_game_filter(False))
        
        # Таймер для автоматического обновления статуса
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Обновляем каждые 5 секунд
        
        # Инициализация
        self.update_status()
        
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
    
    def get_status_style(self, status_type):
        """Get status label style based on status type"""
        styles = {
            "enabled": """
                color: #28a745;
                font-weight: bold;
                padding: 8px;
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                border-radius: 4px;
            """,
            "disabled": """
                color: #dc3545;
                font-weight: bold;
                padding: 8px;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 4px;
            """,
            "unknown": """
                color: #6c757d;
                font-weight: bold;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            """
        }
        return styles.get(status_type, styles["unknown"])
        
    def init_ui(self):
        """Инициализирует пользовательский интерфейс вкладки."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(24)
        
        # Заголовок
        title_label = QLabel("🎮 Игровой фильтр")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #333333;")
        title_label.setWordWrap(True)
        layout.addWidget(title_label)
        
        # Группа управления
        group = QGroupBox("Управление игровым фильтром")
        group.setStyleSheet(self.get_group_style())
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(16)
        
        # Статус
        status_layout = QHBoxLayout()
        status_layout.setSpacing(12)
        self.status_label = QLabel("Статус: Проверяется...")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(36)
        self.status_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.status_label.setStyleSheet(self.get_status_style("unknown"))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        self.start_btn = QPushButton("▶ Включить")
        self.stop_btn = QPushButton("⏹ Отключить")
        
        for btn in [self.start_btn, self.stop_btn]:
            btn.setMinimumWidth(130)
            btn.setMinimumHeight(36)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self.start_btn.setStyleSheet(self.get_button_style("success"))
        self.stop_btn.setStyleSheet(self.get_button_style("danger"))
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        
        group_layout.addLayout(status_layout)
        group_layout.addLayout(btn_layout)
        layout.addWidget(group)
        layout.addStretch()
        
        # Группа информации
        info_group = QGroupBox("📋 Информация")
        info_group.setStyleSheet(self.get_group_style())
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(8)
        
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        self.info_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #333333;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                font-size: 9pt;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        
        info_layout.addWidget(self.info_text)
        info_group.setLayout(info_layout)
        
        # Добавляем все в основной layout
        layout.addWidget(info_group)
        layout.addStretch()
        
    def set_operation_mode(self, in_progress=True):
        """Set operation mode to disable/enable buttons during operations"""
        self.is_operation_in_progress = in_progress
        self.start_btn.setEnabled(not in_progress)
        self.stop_btn.setEnabled(not in_progress)
        
    def update_status(self):
        """Обновляет отображение статуса игрового фильтра."""
        if self.is_operation_in_progress:
            return
            
        try:
            is_enabled = self.is_game_filter_enabled()
            
            # Обновляем статус
            if is_enabled:
                self.status_label.setText("Статус: Включен")
                self.status_label.setStyleSheet(self.get_status_style("enabled"))
            else:
                self.status_label.setText("Статус: Отключен")
                self.status_label.setStyleSheet(self.get_status_style("disabled"))
            
            # Обновляем состояние кнопок
            self.start_btn.setEnabled(not is_enabled and not self.is_operation_in_progress)
            self.stop_btn.setEnabled(is_enabled and not self.is_operation_in_progress)
            
            # Обновляем информацию
            self.update_info_text(is_enabled)
            
        except Exception as e:
            print(f"Ошибка обновления статуса игрового фильтра: {e}")
            self.status_label.setText("Статус: Ошибка проверки")
            self.status_label.setStyleSheet(self.get_status_style("unknown"))
    
    def update_info_text(self, is_enabled):
        """Обновляет информационный текст"""
        try:
            game_filter_file = self.file_manager.bin_dir / "game_filter.enabled"
            file_exists = game_filter_file.exists()
            file_size = game_filter_file.stat().st_size if file_exists else 0
            
            info_text = f"""🎮 Игровой фильтр (Game Filter)

📋 Описание:
Game Filter позволяет обходить блокировки в играх и других сервисах, 
использующих UDP на портах выше 1023.

🔧 Принцип работы:
• При включении создается файл game_filter.enabled
• При отключении файл удаляется
• Фильтр применяется к портам 1024-65535

📊 Текущий статус: {'ВКЛЮЧЕН' if is_enabled else 'ОТКЛЮЧЕН'}
📁 Файл: {'Существует' if file_exists else 'Не существует'}
📏 Размер: {file_size} байт

⚠️ Важно:
После изменения статуса требуется перезапуск службы для применения изменений.

🔄 Автообновление: Каждые 5 секунд"""
            
            self.info_text.setText(info_text)
            
        except Exception as e:
            print(f"Ошибка обновления информационного текста: {e}")
            self.info_text.setText(f"Ошибка загрузки информации: {str(e)}")
        
    def is_game_filter_enabled(self) -> bool:
        """Проверяет, включен ли Game Filter"""
        try:
            game_filter_file = self.file_manager.bin_dir / "game_filter.enabled"
            return game_filter_file.exists()
        except Exception as e:
            print(f"Ошибка проверки статуса игрового фильтра: {e}")
            return False
        
    def toggle_game_filter(self, enable: bool):
        """Переключает Game Filter созданием/удалением файла."""
        if self.is_operation_in_progress:
            return
            
        try:
            self.set_operation_mode(True)
            
            game_filter_file = self.file_manager.bin_dir / "game_filter.enabled"
            current_status = self.is_game_filter_enabled()
            
            # Проверяем, нужно ли что-то менять
            if enable == current_status:
                QMessageBox.information(
                    self,
                    "Информация",
                    f"Игровой фильтр уже {'включен' if enable else 'отключен'}."
                )
                self.set_operation_mode(False)
                return

            if enable:
                # Включаем фильтр (создаем файл)
                game_filter_file.touch()
                action_text = "включен"
            else:
                # Отключаем фильтр (удаляем файл)
                if game_filter_file.exists():
                    game_filter_file.unlink()
                action_text = "отключен"

            # Обновляем статус
            self.update_status()
            self.filter_changed.emit()

            QMessageBox.information(
                self,
                "Статус изменен",
                f"Игровой фильтр был {action_text}.\n\n"
                "Для применения изменений перезапустите службу."
            )
            
        except PermissionError:
            QMessageBox.critical(
                self,
                "Ошибка прав доступа",
                "Недостаточно прав для изменения игрового фильтра.\n"
                "Запустите приложение от имени администратора."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось переключить игровой фильтр:\n{str(e)}"
            )
        finally:
            self.set_operation_mode(False)
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.status_timer:
            self.status_timer.stop()
        event.accept() 