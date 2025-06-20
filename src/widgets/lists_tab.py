from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
                              QPushButton, QLabel, QTextEdit, QComboBox,
                              QMessageBox, QFileDialog, QInputDialog,
                              QProgressBar, QListWidget, QListWidgetItem,
                              QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
                              QHeaderView, QSizePolicy, QToolButton, QMenu,
                              QFrame, QScrollArea, QGridLayout)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtGui import QTextOption, QFont, QIcon, QPixmap, QAction
import re
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Optional
import requests

from utils.file_manager import FileManager
from utils.style_utils import StyleUtils

class StatCard(QFrame):
    """Карточка для отображения статистики."""
    
    def __init__(self, title, value, parent=None):
        super().__init__(parent)
        self.title = title
        self.value_label = None
        self.init_ui(title, value)
    
    def init_ui(self, title, value):
        """Инициализирует интерфейс карточки."""
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(StyleUtils.get_label_style_material(color="#cccccc"))
        
        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(f"""
            QLabel {{
                color: #8ab4f8;
                font-weight: bold;
                font-size: 16pt;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(self.value_label)

class IpsetUpdateWorker(QObject):
    """Воркер для скачивания ipset списка."""
    finished = Signal(str)
    progress = Signal(int)
    status = Signal(str)

    def __init__(self, url, save_path, parent=None):
        super().__init__(parent)
        self.url = url
        self.save_path = save_path

    def run(self):
        try:
            self.status.emit("🔗 Подключение к серверу...")
            self.progress.emit(10)
            
            response = requests.get(self.url, timeout=30, stream=True)
            response.raise_for_status()
            
            self.status.emit("📥 Загрузка данных...")
            self.progress.emit(30)
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.save_path, 'w', encoding='utf-8') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk.decode('utf-8', errors='ignore'))
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = 30 + int((downloaded / total_size) * 60)
                            self.progress.emit(progress)
            
            self.progress.emit(100)
            self.status.emit("✅ Загрузка завершена")
            self.finished.emit("success")
            
        except requests.RequestException as e:
            self.status.emit(f"❌ Ошибка сети: {e}")
            self.finished.emit(f"Ошибка сети: {e}")
        except IOError as e:
            self.status.emit(f"❌ Ошибка сохранения: {e}")
            self.finished.emit(f"Ошибка сохранения файла: {e}")

class ListsTab(QWidget):
    """Вкладка для управления списками доменов с современным дизайном."""
    list_updated = Signal(str)

    def __init__(self, file_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.main_window = main_window
        self.is_operation_in_progress = False
        
        self.init_ui()
        self.connect_signals()
        
        # Инициализация
        self.current_file = None
        self.refresh_files()
        self.update_ipset_status()
        self.update_stats()
        
    def init_ui(self):
        """Инициализирует пользовательский интерфейс."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Заголовок
        title_label = QLabel("📋 Управление списками доменов")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 24px;
                font-weight: bold;
                color: #ffffff;
                margin-bottom: 10px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        main_layout.addWidget(title_label)
        
        # Создаем сплиттер
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Устанавливаем соотношение размеров
        splitter.setSizes([400, 600])
        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """Создает левую панель с файлами и настройками."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        # Группа управления файлами
        files_group = QGroupBox("📁 Файлы списков")
        files_group.setStyleSheet(StyleUtils.get_group_style())
        files_layout = QVBoxLayout(files_group)
        files_layout.setSpacing(12)
        
        # Список файлов
        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(200)
        self.files_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 8px;
                font-size: 11pt;
                color: #ffffff;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #2d2d2d;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
        """)
        files_layout.addWidget(self.files_list)
        
        # Кнопки управления файлами
        files_btn_layout = QHBoxLayout()
        files_btn_layout.setSpacing(10)
        
        # Создаем выпадающее меню для файлов
        self.files_menu_btn = QToolButton()
        self.files_menu_btn.setText("📁 Действия с файлами")
        self.files_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.files_menu_btn.setStyleSheet(StyleUtils.get_button_style_material("info"))
        
        # Создаем меню файлов
        self.files_menu = QMenu()
        self.files_menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 6px;
                padding: 5px;
                color: #ffffff;
            }
            QMenu::item {
                padding: 10px 20px;
                border-radius: 4px;
                margin: 2px;
            }
            QMenu::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
        """)
        
        # Добавляем действия в меню
        file_actions = [
            ("🔄 Обновить список", self.refresh_files),
            ("➕ Добавить файл", self.add_file),
            ("🗑️ Удалить файл", self.delete_file),
        ]
        
        for text, action in file_actions:
            menu_action = QAction(text, self)
            menu_action.triggered.connect(action)
            self.files_menu.addAction(menu_action)
        
        self.files_menu_btn.setMenu(self.files_menu)
        files_btn_layout.addWidget(self.files_menu_btn)
        files_btn_layout.addStretch()
        
        files_layout.addLayout(files_btn_layout)
        
        # Группа Ipset
        ipset_group = QGroupBox("🌐 Режим Ipset")
        ipset_group.setStyleSheet(StyleUtils.get_group_style())
        ipset_layout = QVBoxLayout(ipset_group)
        ipset_layout.setSpacing(12)
        
        # Статус Ipset
        self.ipset_status_label = QLabel("Статус: Выключен")
        self.ipset_status_label.setStyleSheet("""
            QLabel {
                font-size: 12pt;
                font-weight: bold;
                color: #cccccc;
                padding: 8px;
                background-color: #3c3c3c;
                border-radius: 6px;
                border: 1px solid #505050;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        ipset_layout.addWidget(self.ipset_status_label)
        
        # Кнопки Ipset
        ipset_btn_layout = QHBoxLayout()
        ipset_btn_layout.setSpacing(10)
        
        self.ipset_toggle_btn = QPushButton("Включить")
        self.ipset_toggle_btn.setStyleSheet(StyleUtils.get_button_style_material("primary"))
        self.ipset_toggle_btn.setMinimumHeight(40)
        
        self.ipset_update_btn = QPushButton("🔄 Обновить")
        self.ipset_update_btn.setStyleSheet(StyleUtils.get_button_style_material("secondary"))
        self.ipset_update_btn.setMinimumHeight(40)
        
        ipset_btn_layout.addWidget(self.ipset_toggle_btn)
        ipset_btn_layout.addWidget(self.ipset_update_btn)
        ipset_layout.addLayout(ipset_btn_layout)
        
        # Прогресс бар для обновления
        self.ipset_progress = QProgressBar()
        self.ipset_progress.setVisible(False)
        self.ipset_progress.setStyleSheet(StyleUtils.get_progress_bar_style())
        self.ipset_progress.setMinimumHeight(8)
        ipset_layout.addWidget(self.ipset_progress)
        
        # Статус обновления
        self.ipset_status_text = QLabel("")
        self.ipset_status_text.setStyleSheet(StyleUtils.get_label_style_material(color="#cccccc"))
        self.ipset_status_text.setVisible(False)
        ipset_layout.addWidget(self.ipset_status_text)
        
        # Группа статистики
        stats_group = QGroupBox("📊 Статистика")
        stats_group.setStyleSheet(StyleUtils.get_group_style())
        stats_layout = QGridLayout(stats_group)
        stats_layout.setVerticalSpacing(12)
        stats_layout.setHorizontalSpacing(15)
        
        # Создаем карточки статистики
        self.file_count_card = StatCard("Количество файлов", "0")
        self.total_size_card = StatCard("Общий размер", "0 МБ")
        self.domain_count_card = StatCard("Всего доменов", "0")
        
        stats_layout.addWidget(self.file_count_card, 0, 0)
        stats_layout.addWidget(self.total_size_card, 0, 1)
        stats_layout.addWidget(self.domain_count_card, 1, 0, 1, 2)
        
        # Добавляем все группы в layout
        layout.addWidget(files_group)
        layout.addWidget(ipset_group)
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return panel

    def create_right_panel(self):
        """Создает правую панель с содержимым файла."""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Заголовок области редактирования
        content_header = QLabel("📝 Редактор файла")
        content_header.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
                padding: 5px 0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)
        layout.addWidget(content_header)
        
        # Область редактирования
        self.content_text = QTextEdit()
        self.content_text.setStyleSheet(StyleUtils.get_text_edit_style())
        self.content_text.setWordWrapMode(QTextOption.WrapMode.WrapAnywhere)
        layout.addWidget(self.content_text)
        
        # Кнопки редактирования
        edit_btn_layout = QHBoxLayout()
        edit_btn_layout.setSpacing(10)
        
        self.save_btn = QPushButton("💾 Сохранить")
        self.save_btn.setStyleSheet(StyleUtils.get_button_style_material("success"))
        self.save_btn.setMinimumHeight(40)
        self.save_btn.setEnabled(False)
        
        self.clear_btn = QPushButton("🗑️ Очистить")
        self.clear_btn.setStyleSheet(StyleUtils.get_button_style("warning"))
        self.clear_btn.setMinimumHeight(40)
        
        edit_btn_layout.addStretch()
        edit_btn_layout.addWidget(self.clear_btn)
        edit_btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(edit_btn_layout)
        
        return panel

    def connect_signals(self):
        """Подключает сигналы к слотам."""
        self.files_list.currentItemChanged.connect(self.display_file_content)
        self.save_btn.clicked.connect(self.save_file)
        self.clear_btn.clicked.connect(self.clear_content)
        self.ipset_toggle_btn.clicked.connect(self.toggle_ipset_mode)
        self.ipset_update_btn.clicked.connect(self.update_ipset_list)
        self.content_text.textChanged.connect(self.on_content_changed)

    def on_content_changed(self):
        """Обрабатывает изменение содержимого."""
        self.save_btn.setEnabled(True)

    def clear_content(self):
        """Очищает содержимое редактора."""
        reply = QMessageBox.question(
            self, 
            "🗑️ Очистка содержимого", 
            "Вы уверены, что хотите очистить содержимое файла?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.content_text.clear()
            self.save_btn.setEnabled(False)

    def set_operation_mode(self, in_progress=True):
        """Устанавливает режим операции."""
        self.is_operation_in_progress = in_progress
        self.files_menu_btn.setEnabled(not in_progress)
        self.ipset_toggle_btn.setEnabled(not in_progress)
        self.ipset_update_btn.setEnabled(not in_progress)

    def refresh_files(self):
        """Обновляет список файлов."""
        self.files_list.clear()
        try:
            files = [f for f in os.listdir(self.file_manager.lists_dir) if f.endswith('.txt')]
            self.files_list.addItems(files)
        except FileNotFoundError:
            QMessageBox.warning(self, "⚠️ Ошибка", "Папка со списками не найдена.")

    def display_file_content(self, current, previous):
        """Отображает содержимое выбранного файла."""
        if current:
            file_path = self.file_manager.lists_dir / current.text()
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.content_text.setPlainText(f.read())
                self.content_text.setReadOnly(False)
                self.save_btn.setEnabled(False)
                self.current_file = current.text()
            except Exception as e:
                self.content_text.setPlainText(f"❌ Не удалось прочитать файл: {e}")
                self.content_text.setReadOnly(True)
                self.current_file = None

    def add_file(self):
        """Добавляет новый пустой файл списка."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "➕ Новый список", 
            str(self.file_manager.lists_dir), 
            "Text Files (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    pass
                self.refresh_files()
                QMessageBox.information(self, "✅ Успех", "Файл успешно создан.")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось создать файл: {e}")

    def delete_file(self):
        """Удаляет выбранный файл."""
        current_item = self.files_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "⚠️ Ошибка", "Выберите файл для удаления.")
            return

        reply = QMessageBox.question(
            self, 
            "🗑️ Подтверждение", 
            f"Вы уверены, что хотите удалить файл '{current_item.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(self.file_manager.lists_dir / current_item.text())
                self.refresh_files()
                self.content_text.clear()
                QMessageBox.information(self, "✅ Успех", "Файл успешно удален.")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось удалить файл: {e}")

    def save_file(self):
        """Сохраняет изменения в файле."""
        current_item = self.files_list.currentItem()
        if not current_item:
            return
        
        file_path = self.file_manager.lists_dir / current_item.text()
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.content_text.toPlainText())
            self.save_btn.setEnabled(False)
            self.list_updated.emit(current_item.text())
            self.update_stats()
            QMessageBox.information(self, "✅ Успех", "Файл успешно сохранен.")
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось сохранить файл: {e}")

    def update_ipset_status(self):
        """Обновляет статус режима Ipset."""
        is_enabled = (self.file_manager.lists_dir / "ipset-all.txt").exists()
        
        if is_enabled:
            self.ipset_status_label.setText("Статус: Включен")
            self.ipset_status_label.setStyleSheet("""
                QLabel {
                    font-size: 12pt;
                    font-weight: bold;
                    color: #81c995;
                    padding: 8px;
                    background-color: rgba(129, 201, 149, 0.1);
                    border-radius: 6px;
                    border: 1px solid #81c995;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            self.ipset_toggle_btn.setText("Выключить")
            self.ipset_toggle_btn.setStyleSheet(StyleUtils.get_button_style_material("danger"))
        else:
            self.ipset_status_label.setText("Статус: Выключен")
            self.ipset_status_label.setStyleSheet("""
                QLabel {
                    font-size: 12pt;
                    font-weight: bold;
                    color: #cccccc;
                    padding: 8px;
                    background-color: #3c3c3c;
                    border-radius: 6px;
                    border: 1px solid #505050;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            self.ipset_toggle_btn.setText("Включить")
            self.ipset_toggle_btn.setStyleSheet(StyleUtils.get_button_style_material("primary"))

    def toggle_ipset_mode(self):
        """Переключает режим Ipset."""
        ipset_file = self.file_manager.lists_dir / "ipset-all.txt"
        if ipset_file.exists():
            os.remove(ipset_file)
            QMessageBox.information(self, "✅ Успех", "Режим Ipset выключен.")
        else:
            # Создаем пустой файл, чтобы включить режим
            ipset_file.touch()
            self.update_ipset_list() # Сразу обновляем после включения
            QMessageBox.information(self, "✅ Успех", "Режим Ipset включен.")
        self.update_ipset_status()

    def update_ipset_list(self):
        """Запускает обновление списка ipset-all.txt."""
        if self.is_operation_in_progress:
            return
            
        self.set_operation_mode(True)
        self.ipset_update_btn.setEnabled(False)
        self.ipset_update_btn.setText("🔄 Обновление...")
        self.ipset_progress.setVisible(True)
        self.ipset_status_text.setVisible(True)

        self.ipset_worker_thread = QThread()
        self.ipset_worker = IpsetUpdateWorker(
            url="https://raw.githubusercontent.com/zapret-info/z-i/master/ipset-all.txt",
            save_path=self.file_manager.lists_dir / "ipset-all.txt"
        )
        self.ipset_worker.moveToThread(self.ipset_worker_thread)

        if self.main_window:
            self.main_window.register_thread(self.ipset_worker_thread)

        self.ipset_worker.finished.connect(self.on_ipset_update_finished)
        self.ipset_worker.progress.connect(self.ipset_progress.setValue)
        self.ipset_worker.status.connect(self.ipset_status_text.setText)
        self.ipset_worker_thread.started.connect(self.ipset_worker.run)
        self.ipset_worker_thread.finished.connect(self.ipset_worker_thread.deleteLater)
        self.ipset_worker.finished.connect(self.ipset_worker.deleteLater)
        self.ipset_worker_thread.finished.connect(lambda: self.set_operation_mode(False))
        self.ipset_worker_thread.start()

    def on_ipset_update_finished(self, status):
        """Обрабатывает завершение обновления ipset."""
        self.ipset_progress.setVisible(False)
        self.ipset_status_text.setVisible(False)
        
        if status == "success":
            QMessageBox.information(self, "✅ Успех", "Список Ipset успешно обновлен.")
        else:
            QMessageBox.warning(self, "⚠️ Ошибка обновления", status)
            
        self.ipset_update_btn.setEnabled(True)
        self.ipset_update_btn.setText("🔄 Обновить")
        self.update_stats()

    def update_stats(self):
        """Обновляет статистику по файлам."""
        if not hasattr(self, 'file_count_card') or not hasattr(self, 'total_size_card') or not hasattr(self, 'domain_count_card'):
            return

        try:
            total_size = 0
            total_domains = 0
            
            list_files = [f for f in os.listdir(self.file_manager.lists_dir) if f.endswith('.txt')]
            
            for filename in list_files:
                filepath = self.file_manager.lists_dir / filename
                total_size += os.path.getsize(filepath)
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    total_domains += len(f.readlines())
            
            # Обновляем карточки статистики
            self.file_count_card.value_label.setText(str(len(list_files)))
            self.total_size_card.value_label.setText(f"{total_size / (1024*1024):.2f} МБ")
            self.domain_count_card.value_label.setText(str(total_domains))
            
        except Exception as e:
            self.file_count_card.value_label.setText("Ошибка")
            self.total_size_card.value_label.setText("Ошибка")
            self.domain_count_card.value_label.setText("Ошибка")
            print(f"Ошибка при обновлении статистики: {e}")

    def stop_threads(self):
        """Останавливает фоновые потоки."""
        if hasattr(self, 'ipset_worker_thread') and self.ipset_worker_thread.isRunning():
            self.ipset_worker_thread.quit()
            self.ipset_worker_thread.wait(2000) 