from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QCheckBox, QComboBox,
                              QFileDialog, QMessageBox, QGroupBox, QFormLayout,
                              QToolButton, QMenu, QFrame, QGridLayout,
                              QScrollArea, QSplitter)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QIcon, QAction
import os
from pathlib import Path
import winreg

from utils.file_manager import FileManager
from utils.process_manager import ProcessManager
from utils.config_manager import ConfigManager
from utils.update_checker import UpdateChecker
from utils.style_utils import StyleUtils

class SettingsTab(QWidget):
    """Вкладка для настроек приложения с современным дизайном."""
    settings_changed = Signal()

    def __init__(self, file_manager, process_manager, config_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.process_manager = process_manager
        self.config_manager = config_manager
        self.main_window = main_window
        
        self.init_ui()
        
        # Подключаем сигналы
        self.auto_update_checkbox.stateChanged.connect(self.on_settings_changed)
        self.startup_checkbox.stateChanged.connect(self.on_settings_changed)
        self.minimize_checkbox.stateChanged.connect(self.on_settings_changed)
        self.theme_combo.currentIndexChanged.connect(self.on_settings_changed)
        self.theme_combo.currentIndexChanged.connect(self.settings_changed)
        
        self.check_update_btn.clicked.connect(self.check_updates)
        self.save_btn.clicked.connect(self.save_settings)
        self.reset_btn.clicked.connect(self.load_settings)
        
        # Инициализация
        self.load_settings()
        
    def init_ui(self):
        """Инициализирует пользовательский интерфейс вкладки."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Заголовок
        title_label = QLabel("⚙️ Настройки приложения")
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
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель с настройками
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель с действиями
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        # Устанавливаем соотношение размеров
        splitter.setSizes([600, 300])
        main_layout.addWidget(splitter)

    def create_left_panel(self):
        """Создает левую панель с настройками."""
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
        layout.setSpacing(20)
        
        # Группа настроек темы
        theme_group = QGroupBox("🎨 Настройки темы")
        theme_group.setStyleSheet(StyleUtils.get_group_style())
        theme_layout = QGridLayout(theme_group)
        theme_layout.setVerticalSpacing(12)
        theme_layout.setHorizontalSpacing(15)
        
        theme_label = QLabel("Тема интерфейса:")
        theme_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Темная", "Светлая", "Material Dark", "Material Light"])
        self.theme_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
                min-height: 35px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                margin-right: 10px;
            }
        """)
        
        theme_layout.addWidget(theme_label, 0, 0)
        theme_layout.addWidget(self.theme_combo, 0, 1)
        
        # Группа настроек обновлений
        update_group = QGroupBox("🔄 Настройки обновлений")
        update_group.setStyleSheet(StyleUtils.get_group_style())
        update_layout = QVBoxLayout(update_group)
        update_layout.setSpacing(15)
        
        self.auto_update_checkbox = QCheckBox("Проверять обновления при запуске")
        self.auto_update_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border-color: #1976d2;
            }
        """)
        
        self.check_update_btn = QPushButton("🔍 Проверить обновления")
        self.check_update_btn.setStyleSheet(StyleUtils.get_button_style("secondary"))
        self.check_update_btn.setMinimumHeight(40)
        self.check_update_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        update_layout.addWidget(self.auto_update_checkbox)
        update_layout.addWidget(self.check_update_btn)
        
        # Группа настроек приложения
        app_group = QGroupBox("🚀 Настройки приложения")
        app_group.setStyleSheet(StyleUtils.get_group_style())
        app_layout = QVBoxLayout(app_group)
        app_layout.setSpacing(15)
        
        self.startup_checkbox = QCheckBox("Запускать при запуске Windows")
        self.startup_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border-color: #1976d2;
            }
        """)
        
        self.minimize_checkbox = QCheckBox("Сворачивать в трей при закрытии")
        self.minimize_checkbox.setStyleSheet("""
            QCheckBox {
                font-size: 11pt;
                color: #333333;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #dee2e6;
                border-radius: 4px;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border-color: #1976d2;
            }
        """)
        
        app_layout.addWidget(self.startup_checkbox)
        app_layout.addWidget(self.minimize_checkbox)
        
        # Добавляем все группы
        layout.addWidget(theme_group)
        layout.addWidget(update_group)
        layout.addWidget(app_group)
        layout.addStretch()
        
        return panel

    def create_right_panel(self):
        """Создает правую панель с действиями."""
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
        layout.setSpacing(20)
        
        # Заголовок действий
        actions_header = QLabel("🎮 Действия")
        actions_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1c1b1f;
                padding: 5px 0;
            }
        """)
        layout.addWidget(actions_header)
        
        # Кнопки управления
        self.save_btn = QPushButton("💾 Сохранить настройки")
        self.save_btn.setStyleSheet(StyleUtils.get_button_style("success"))
        self.save_btn.setMinimumHeight(45)
        self.save_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.save_btn.setEnabled(False)
        
        self.reset_btn = QPushButton("🔄 Сбросить настройки")
        self.reset_btn.setStyleSheet(StyleUtils.get_button_style("warning"))
        self.reset_btn.setMinimumHeight(45)
        self.reset_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        # Создаем выпадающее меню для дополнительных действий
        self.actions_menu_btn = QToolButton()
        self.actions_menu_btn.setText("📋 Дополнительные действия")
        self.actions_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_menu_btn.setStyleSheet("""
            QToolButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 10pt;
                min-height: 40px;
            }
            QToolButton:hover {
                background-color: #1565c0;
            }
            QToolButton:pressed {
                background-color: #0d47a1;
            }
        """)
        
        # Создаем меню действий
        self.actions_menu = QMenu()
        self.actions_menu.setStyleSheet("""
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
            ("📤 Экспорт настроек", self.export_settings),
            ("📥 Импорт настроек", self.import_settings),
            ("🔧 Сбросить все настройки", self.reset_all_settings)
        ]
        
        for text, action in actions:
            menu_action = QAction(text, self)
            menu_action.triggered.connect(action)
            self.actions_menu.addAction(menu_action)
        
        self.actions_menu_btn.setMenu(self.actions_menu)
        
        # Информационная панель
        info_group = QGroupBox("ℹ️ Информация")
        info_group.setStyleSheet(StyleUtils.get_group_style())
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(10)
        
        info_text = QLabel("""
        <b>💡 Подсказки:</b><br>
        • Изменения темы применяются сразу<br>
        • Автозапуск требует прав администратора<br>
        • Настройки сохраняются автоматически<br>
        • Используйте экспорт для резервных копий
        """)
        info_text.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #666666;
                line-height: 1.4;
            }
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        # Добавляем все элементы
        layout.addWidget(self.save_btn)
        layout.addWidget(self.reset_btn)
        layout.addWidget(self.actions_menu_btn)
        layout.addWidget(info_group)
        layout.addStretch()
        
        return panel
        
    def load_settings(self):
        """Загружает настройки"""
        # Тема
        theme = self.config_manager.get("general", "theme", "Темная")
        self.theme_combo.setCurrentText(theme)
        
        # Автозапуск
        autostart = self.config_manager.get("service", "autostart", False)
        self.startup_checkbox.setChecked(autostart)
        
        # Запуск свёрнутым
        start_minimized = self.config_manager.get("general", "start_minimized", False)
        self.minimize_checkbox.setChecked(start_minimized)
        
        # Проверка обновлений
        auto_update = self.config_manager.get("updates", "auto_update", False)
        self.auto_update_checkbox.setChecked(auto_update)
        
        # Отключаем кнопку сохранения
        self.save_btn.setEnabled(False)
        
    def save_settings(self):
        """Сохраняет настройки"""
        try:
            # Тема
            theme = self.theme_combo.currentText()
            self.config_manager.set("general", "theme", theme)
            
            # Автозапуск
            self.config_manager.set("service", "autostart", self.startup_checkbox.isChecked())
            
            # Запуск свёрнутым
            self.config_manager.set("general", "start_minimized", self.minimize_checkbox.isChecked())
            
            # Проверка обновлений
            self.config_manager.set("updates", "auto_update", self.auto_update_checkbox.isChecked())
            
            # Обновляем автозапуск в реестре
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE
                )
                
                if self.startup_checkbox.isChecked():
                    service_path = str(self.file_manager.base_dir / "service.bat")
                    winreg.SetValueEx(
                        key,
                        "ZapretService",
                        0,
                        winreg.REG_SZ,
                        f'"{service_path}"'
                    )
                else:
                    try:
                        winreg.DeleteValue(key, "ZapretService")
                    except FileNotFoundError:
                        pass  # Значение уже удалено
                        
                winreg.CloseKey(key)
            except Exception as e:
                print(f"Ошибка обновления автозапуска: {e}")
            
            # Сохраняем конфигурацию
            self.config_manager.save_config()
            
            # Отключаем кнопку сохранения
            self.save_btn.setEnabled(False)
            
            QMessageBox.information(self, "✅ Успех", "Настройки сохранены!")
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось сохранить настройки: {e}")
            
    def reset_all_settings(self):
        """Сбрасывает все настройки к значениям по умолчанию."""
        reply = QMessageBox.question(
            self, 
            "🔄 Сброс настроек", 
            "Вы уверены, что хотите сбросить все настройки к значениям по умолчанию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Сбрасываем настройки к значениям по умолчанию
                self.config_manager.reset_to_defaults()
                self.load_settings()
                self.settings_changed.emit()
                QMessageBox.information(self, "✅ Успех", "Все настройки сброшены к значениям по умолчанию.")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось сбросить настройки: {e}")
        
    def on_settings_changed(self):
        """Обработчик изменения настроек"""
        self.save_btn.setEnabled(True)
        
    def check_updates(self):
        """Проверяет наличие обновлений."""
        self.check_update_btn.setEnabled(False)
        self.check_update_btn.setText("🔍 Проверка...")

        self.update_thread = QThread()
        if self.main_window:
            self.main_window.register_thread(self.update_thread)
        self.update_checker = UpdateChecker()
        self.update_checker.moveToThread(self.update_thread)

        self.update_checker.result.connect(self.on_update_check_finished)
        self.update_thread.started.connect(self.update_checker.run)
        self.update_thread.finished.connect(self.update_thread.deleteLater)
        self.update_checker.result.connect(self.update_thread.quit)
        
        self.update_thread.start()

    def on_update_check_finished(self, new_version, url):
        """Обрабатывает результат проверки обновлений."""
        self.check_update_btn.setEnabled(True)
        self.check_update_btn.setText("🔍 Проверить обновления")

        if new_version and new_version != "error":
            reply = QMessageBox.information(
                self, 
                "🆕 Доступно обновление", 
                f"Доступна новая версия: {new_version}\nХотите перейти на страницу загрузки?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                import webbrowser
                webbrowser.open(url)
        elif new_version == "error":
            QMessageBox.warning(self, "⚠️ Ошибка", "Не удалось проверить обновления. Проверьте подключение к интернету.")
        else:
            QMessageBox.information(self, "ℹ️ Обновления", "У вас установлена последняя версия.")
        
    def export_settings(self):
        """Экспортирует текущие настройки в файл."""
        # Убедимся, что текущие настройки сохранены перед экспортом
        if self.save_btn.isEnabled():
            reply = QMessageBox.question(
                self, 
                "💾 Сохранение настроек", 
                "У вас есть несохраненные изменения. Хотите сохранить их перед экспортом?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_settings()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "📤 Экспорт настроек", 
            "zapret_settings.json", 
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.config_manager.export_config(file_path)
                QMessageBox.information(self, "✅ Успех", f"Настройки успешно экспортированы в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка экспорта", f"Не удалось экспортировать настройки: {e}")

    def import_settings(self):
        """Импортирует настройки из файла."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "📥 Импорт настроек", 
            "", 
            "JSON Files (*.json)"
        )
        if file_path:
            try:
                self.config_manager.import_config(file_path)
                self.load_settings()  # Перезагружаем UI с новыми настройками
                self.settings_changed.emit() # Уведомляем главное окно об изменениях
                QMessageBox.information(self, "✅ Успех", "Настройки успешно импортированы. Рекомендуется перезапустить приложение.")
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка импорта", f"Не удалось импортировать настройки: {e}") 