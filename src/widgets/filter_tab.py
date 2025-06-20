import os
import subprocess
import json
from pathlib import Path
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                               QPushButton, QLabel, QComboBox, QTextEdit, 
                               QCheckBox, QSpinBox, QProgressBar, QFrame,
                               QScrollArea, QGridLayout, QSplitter, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
from utils.style_utils import StyleUtils

class FilterTab(QWidget):
    def __init__(self, file_manager, process_manager, main_window=None):
        super().__init__()
        self.file_manager = file_manager
        self.process_manager = process_manager
        self.main_window = main_window
        self.is_operation_in_progress = False
        self.init_ui()
        self.load_settings()  # Load saved settings after UI initialization
        
    def init_ui(self):
        """Initialize Dark Theme UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)
        
        # Create scrollable area for better responsiveness
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)
        
        # Dark Theme Cards
        self.create_profile_card(content_layout)
        self.create_settings_card(content_layout)
        self.create_status_card(content_layout)
        self.create_actions_card(content_layout)
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def get_card_style(self):
        """Get common card style to avoid duplication"""
        return """
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                font-size: 16px;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 12px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
    
    def get_label_style(self, color="#ffffff", weight="500"):
        """Get common label style"""
        return f"""
            QLabel {{
                color: {color};
                font-weight: {weight};
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """
    
    def get_combo_style(self):
        """Get common combobox style"""
        return """
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                min-height: 20px;
                min-width: 200px;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
                border-width: 2px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
        """
    
    def get_button_style(self, button_type="secondary"):
        """Get button style based on type"""
        styles = {
            "success": """
                QPushButton {
                    background-color: #4caf50;
                    color: #ffffff;
                    border: none;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #888888;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #888888;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: transparent;
                    color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QPushButton:disabled {
                    background-color: #2d2d2d;
                    color: #666666;
                    border-color: #404040;
                }
            """
        }
        return styles.get(button_type, styles["secondary"])
    
    def get_status_style(self, status_type):
        """Get status label style based on status type"""
        colors = {
            "success": "#4caf50",
            "error": "#f44336", 
            "warning": "#ff9800",
            "info": "#2196f3"
        }
        color = colors.get(status_type, "#ffffff")
        return f"""
            QLabel {{
                color: {color};
                font-weight: 600;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """
        
    def create_profile_card(self, parent_layout):
        """Create Material Design profile selection card"""
        card = QGroupBox("📊 Профиль фильтрации")
        card.setProperty("elevation", "1")
        card.setStyleSheet(self.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Profile selection
        profile_layout = QHBoxLayout()
        profile_layout.setSpacing(16)
        
        profile_label = QLabel("Выберите профиль:")
        profile_label.setStyleSheet(self.get_label_style())
        
        self.profile_combo = QComboBox()
        self.profile_combo.setStyleSheet(self.get_combo_style())
        
        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.profile_combo)
        profile_layout.addStretch()
        
        layout.addLayout(profile_layout)
        
        # Profile description
        self.profile_description = QLabel("Выберите профиль для просмотра описания")
        self.profile_description.setStyleSheet(self.get_label_style("#666666", "400"))
        self.profile_description.setWordWrap(True)
        layout.addWidget(self.profile_description)
        
        parent_layout.addWidget(card)
        
        # Load profiles
        self.load_profiles()
        
    def create_settings_card(self, parent_layout):
        """Create Material Design settings card"""
        card = QGroupBox("⚙️ Настройки фильтра")
        card.setProperty("elevation", "1")
        card.setStyleSheet(self.get_card_style())
        
        layout = QGridLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Settings grid
        row = 0
        
        # Auto-start setting
        self.auto_start_check = QCheckBox("Автозапуск при старте системы")
        self.auto_start_check.setStyleSheet("""
            QCheckBox {
                color: #1c1b1f;
                font-size: 14px;
                spacing: 12px;
            }
        """)
        layout.addWidget(self.auto_start_check, row, 0, 1, 2)
        row += 1
        
        # Minimize to tray setting
        self.minimize_tray_check = QCheckBox("Сворачивать в трей")
        self.minimize_tray_check.setStyleSheet("""
            QCheckBox {
                color: #1c1b1f;
                font-size: 14px;
                spacing: 12px;
            }
        """)
        layout.addWidget(self.minimize_tray_check, row, 0, 1, 2)
        row += 1
        
        # Logging setting
        self.logging_check = QCheckBox("Включить логирование")
        self.logging_check.setStyleSheet("""
            QCheckBox {
                color: #1c1b1f;
                font-size: 14px;
                spacing: 12px;
            }
        """)
        layout.addWidget(self.logging_check, row, 0, 1, 2)
        row += 1
        
        # Log level
        log_level_label = QLabel("Уровень логирования:")
        log_level_label.setStyleSheet(self.get_label_style())
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        self.log_level_combo.setStyleSheet(self.get_combo_style())
        
        layout.addWidget(log_level_label, row, 0)
        layout.addWidget(self.log_level_combo, row, 1)
        row += 1
        
        parent_layout.addWidget(card)
        
    def create_status_card(self, parent_layout):
        """Create Material Design status card"""
        card = QGroupBox("📈 Статус фильтра")
        card.setProperty("elevation", "1")
        card.setStyleSheet(self.get_card_style())
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Status indicators
        status_grid = QGridLayout()
        status_grid.setSpacing(16)
        
        # Service status
        service_status_label = QLabel("Служба:")
        service_status_label.setStyleSheet(self.get_label_style())
        
        self.service_status = QLabel("Неизвестно")
        self.service_status.setProperty("status", "warning")
        self.service_status.setStyleSheet(self.get_status_style("warning"))
        
        status_grid.addWidget(service_status_label, 0, 0)
        status_grid.addWidget(self.service_status, 0, 1)
        
        # Filter status
        filter_status_label = QLabel("Фильтр:")
        filter_status_label.setStyleSheet(self.get_label_style())
        
        self.filter_status = QLabel("Неактивен")
        self.filter_status.setProperty("status", "error")
        self.filter_status.setStyleSheet(self.get_status_style("error"))
        
        status_grid.addWidget(filter_status_label, 1, 0)
        status_grid.addWidget(self.filter_status, 1, 1)
        
        # Active profile
        active_profile_label = QLabel("Активный профиль:")
        active_profile_label.setStyleSheet(self.get_label_style())
        
        self.active_profile = QLabel("Нет")
        self.active_profile.setStyleSheet(self.get_label_style("#666666", "500"))
        
        status_grid.addWidget(active_profile_label, 2, 0)
        status_grid.addWidget(self.active_profile, 2, 1)
        
        layout.addLayout(status_grid)
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #f5f5f5;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: #1c1b1f;
                font-weight: 500;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #1976d2;
                border-radius: 8px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        parent_layout.addWidget(card)
        
    def create_actions_card(self, parent_layout):
        """Create Material Design actions card"""
        card = QGroupBox("🎯 Действия")
        card.setProperty("elevation", "1")
        card.setStyleSheet(self.get_card_style())
        
        layout = QHBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Action buttons
        self.start_button = QPushButton("▶️ Запустить")
        self.start_button.setProperty("type", "success")
        self.start_button.setStyleSheet(self.get_button_style("success"))
        
        self.stop_button = QPushButton("⏹️ Остановить")
        self.stop_button.setProperty("type", "danger")
        self.stop_button.setStyleSheet(self.get_button_style("danger"))
        
        self.restart_button = QPushButton("🔄 Перезапустить")
        self.restart_button.setProperty("type", "secondary")
        self.restart_button.setStyleSheet(self.get_button_style("secondary"))
        
        self.apply_button = QPushButton("💾 Применить настройки")
        self.apply_button.setProperty("type", "secondary")
        self.apply_button.setStyleSheet(self.get_button_style("secondary"))
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
        layout.addWidget(self.restart_button)
        layout.addWidget(self.apply_button)
        layout.addStretch()
        
        parent_layout.addWidget(card)
        
        # Connect signals
        self.start_button.clicked.connect(self.start_filter)
        self.stop_button.clicked.connect(self.stop_filter)
        self.restart_button.clicked.connect(self.restart_filter)
        self.apply_button.clicked.connect(self.apply_settings)
        self.profile_combo.currentTextChanged.connect(self.on_profile_changed)
        
        # Start status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(5000)  # Update every 5 seconds
        
        # Initial status update
        self.update_status()
        
    def load_profiles(self):
        """Load available filter profiles"""
        try:
            bat_files = self.file_manager.get_bat_files()
            profiles = []
            
            for bat_file in bat_files:
                filename = os.path.basename(bat_file)
                if filename.endswith('.bat'):
                    profile_name = filename[:-4]  # Remove .bat extension
                    profiles.append(profile_name)
            
            self.profile_combo.clear()
            if profiles:
                self.profile_combo.addItems(profiles)
                self.profile_combo.setCurrentIndex(0)
                self.on_profile_changed(profiles[0])
            else:
                self.profile_description.setText("Профили не найдены")
                
        except Exception as e:
            print(f"Error loading profiles: {e}")
            self.profile_description.setText("Ошибка загрузки профилей")
    
    def on_profile_changed(self, profile_name):
        """Handle profile selection change"""
        if not profile_name:
            self.profile_description.setText("Выберите профиль для просмотра описания")
            return
            
        # Generate description based on profile name
        descriptions = {
            "general": "Основной профиль фильтрации для всех типов трафика",
            "general (ALT)": "Альтернативный профиль с дополнительными настройками",
            "general (ALT2)": "Второй альтернативный профиль",
            "general (ALT3)": "Третий альтернативный профиль", 
            "general (ALT4)": "Четвертый альтернативный профиль",
            "general (ALT5)": "Пятый альтернативный профиль",
            "general (FAKE TLS MOD)": "Профиль с поддержкой Fake TLS для обхода блокировок",
            "general (FAKE TLS MOD ALT)": "Альтернативный Fake TLS профиль",
            "general (FAKE TLS MOD AUTO)": "Автоматический Fake TLS профиль",
            "general (МГТС)": "Специализированный профиль для сети МГТС",
            "general (МГТС2)": "Второй профиль для сети МГТС"
        }
        
        description = descriptions.get(profile_name, f"Профиль: {profile_name}")
        self.profile_description.setText(description)
    
    def update_status(self):
        """Update filter and service status"""
        if self.is_operation_in_progress:
            return  # Don't update during operations
            
        try:
            service_status = self.check_service_status()
            self.update_status_display(service_status)
                
        except Exception as e:
            print(f"Error updating status: {e}")
            self.update_status_display("Ошибка проверки статуса")
    
    def update_status_display(self, service_status):
        """Update status display based on service status"""
        # Update service status
        if "работает" in service_status.lower() or "running" in service_status.lower():
            self.service_status.setText("Запущена")
            self.service_status.setProperty("status", "success")
            self.service_status.setStyleSheet(self.get_status_style("success"))
        elif "остановлена" in service_status.lower() or "stopped" in service_status.lower():
            self.service_status.setText("Остановлена")
            self.service_status.setProperty("status", "error")
            self.service_status.setStyleSheet(self.get_status_style("error"))
        elif "не установлена" in service_status.lower():
            self.service_status.setText("Не установлена")
            self.service_status.setProperty("status", "warning")
            self.service_status.setStyleSheet(self.get_status_style("warning"))
        else:
            self.service_status.setText("Неизвестно")
            self.service_status.setProperty("status", "warning")
            self.service_status.setStyleSheet(self.get_status_style("warning"))
        
        # Update filter status
        if "работает" in service_status.lower() or "running" in service_status.lower():
            self.filter_status.setText("Активен")
            self.filter_status.setProperty("status", "success")
            self.filter_status.setStyleSheet(self.get_status_style("success"))
        else:
            self.filter_status.setText("Неактивен")
            self.filter_status.setProperty("status", "error")
            self.filter_status.setStyleSheet(self.get_status_style("error"))
        
        # Update active profile
        if ("работает" in service_status.lower() or "running" in service_status.lower()) and self.profile_combo.currentText():
            self.active_profile.setText(self.profile_combo.currentText())
        else:
            self.active_profile.setText("Нет")
    
    def check_service_status(self):
        """Проверяет статус службы Windows"""
        try:
            # Проверяем службу 'zapret'
            result = subprocess.run(
                ['sc', 'query', 'zapret'], 
                capture_output=True, 
                text=True, 
                encoding='cp866'
            )
            
            if result.returncode == 0:
                # Служба найдена, парсим её статус
                for line in result.stdout.split('\n'):
                    if 'STATE' in line.upper():
                        if 'RUNNING' in line.upper():
                            return "Работает (служба zapret)"
                        elif 'STOPPED' in line.upper():
                            return "Остановлена (служба zapret)"
                        elif 'STARTING' in line.upper():
                            return "Запускается (служба zapret)"
                        elif 'STOPPING' in line.upper():
                            return "Останавливается (служба zapret)"
                        else:
                            return f"Неизвестно (служба zapret)"
            
            # Если служба не найдена, проверяем процесс winws.exe
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq winws.exe'], 
                capture_output=True, 
                text=True, 
                encoding='cp866'
            )
            
            if result.returncode == 0 and 'winws.exe' in result.stdout:
                return "Работает (процесс winws.exe)"
            
            # Если ни служба, ни процесс не найдены
            return "Служба не установлена"
            
        except Exception as e:
            return f"Ошибка: {str(e)}"
    
    def set_operation_mode(self, in_progress=True):
        """Set operation mode to disable/enable buttons during operations"""
        self.is_operation_in_progress = in_progress
        self.start_button.setEnabled(not in_progress)
        self.stop_button.setEnabled(not in_progress)
        self.restart_button.setEnabled(not in_progress)
        self.apply_button.setEnabled(not in_progress)
        self.profile_combo.setEnabled(not in_progress)
        
        if in_progress:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # Indeterminate progress
        else:
            self.progress_bar.setVisible(False)
    
    def start_filter(self):
        """Start the filter service"""
        if self.is_operation_in_progress:
            return
            
        try:
            profile = self.profile_combo.currentText()
            if not profile:
                QMessageBox.warning(self, "Предупреждение", "Выберите профиль для запуска")
                return
                
            self.set_operation_mode(True)
            
            # Start service in background
            profile_path = self.file_manager.base_dir / f"{profile}.bat"
            if profile_path.exists():
                success = self.process_manager.run_bat(str(profile_path), wait=False)
                if not success:
                    QMessageBox.critical(self, "Ошибка", "Не удалось запустить профиль")
                    self.set_operation_mode(False)
                    return
            else:
                QMessageBox.critical(self, "Ошибка", f"Файл профиля {profile}.bat не найден")
                self.set_operation_mode(False)
                return
            
            # Update status after delays
            QTimer.singleShot(2000, self.update_status)
            QTimer.singleShot(3000, lambda: self.set_operation_mode(False))
            
        except Exception as e:
            print(f"Error starting filter: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка запуска фильтра: {str(e)}")
            self.set_operation_mode(False)
    
    def stop_filter(self):
        """Stop the filter service"""
        if self.is_operation_in_progress:
            return
            
        try:
            self.set_operation_mode(True)
            
            # Try to stop service first
            try:
                subprocess.run(['sc', 'stop', 'zapret'], capture_output=True, text=True, encoding='cp866')
            except:
                pass  # Service might not exist
            
            # Kill process
            success = self.process_manager.kill_process("winws.exe")
            if not success:
                QMessageBox.warning(self, "Предупреждение", "Не удалось остановить процесс winws.exe")
            
            # Update status after delays
            QTimer.singleShot(2000, self.update_status)
            QTimer.singleShot(3000, lambda: self.set_operation_mode(False))
            
        except Exception as e:
            print(f"Error stopping filter: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка остановки фильтра: {str(e)}")
            self.set_operation_mode(False)
    
    def restart_filter(self):
        """Restart the filter service"""
        if self.is_operation_in_progress:
            return
            
        try:
            self.set_operation_mode(True)
            
            # Stop first
            self.stop_filter()
            
            # Start after delay
            QTimer.singleShot(4000, self.start_filter)
            
        except Exception as e:
            print(f"Error restarting filter: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка перезапуска фильтра: {str(e)}")
            self.set_operation_mode(False)
    
    def apply_settings(self):
        """Apply current settings"""
        try:
            # Create settings dictionary
            settings = {
                "auto_start": self.auto_start_check.isChecked(),
                "minimize_tray": self.minimize_tray_check.isChecked(),
                "logging_enabled": self.logging_check.isChecked(),
                "log_level": self.log_level_combo.currentText(),
                "selected_profile": self.profile_combo.currentText()
            }
            
            # Save to config file
            config_path = self.file_manager.base_dir / "filter_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            # Show success message
            QMessageBox.information(self, "Успех", "Настройки успешно применены и сохранены")
            
            # Apply auto-start setting if needed
            if settings["auto_start"]:
                self.setup_autostart()
            else:
                self.remove_autostart()
                
        except Exception as e:
            print(f"Error applying settings: {e}")
            QMessageBox.critical(self, "Ошибка", f"Ошибка применения настроек: {str(e)}")
    
    def setup_autostart(self):
        """Setup application autostart"""
        try:
            # This would typically add the app to Windows startup
            # For now, just create a placeholder
            autostart_path = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
            autostart_path.mkdir(parents=True, exist_ok=True)
            print("Autostart setup completed")
        except Exception as e:
            print(f"Error setting up autostart: {e}")
    
    def remove_autostart(self):
        """Remove application from autostart"""
        try:
            # This would typically remove the app from Windows startup
            print("Autostart removal completed")
        except Exception as e:
            print(f"Error removing autostart: {e}")
    
    def load_settings(self):
        """Load saved settings"""
        try:
            config_path = self.file_manager.base_dir / "filter_config.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Apply settings to UI
                self.auto_start_check.setChecked(settings.get("auto_start", False))
                self.minimize_tray_check.setChecked(settings.get("minimize_tray", False))
                self.logging_check.setChecked(settings.get("logging_enabled", False))
                
                log_level = settings.get("log_level", "INFO")
                index = self.log_level_combo.findText(log_level)
                if index >= 0:
                    self.log_level_combo.setCurrentIndex(index)
                
                # Set profile if it exists
                profile = settings.get("selected_profile", "")
                if profile:
                    index = self.profile_combo.findText(profile)
                    if index >= 0:
                        self.profile_combo.setCurrentIndex(index)
                        
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.status_timer:
            self.status_timer.stop()
        event.accept() 