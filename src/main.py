import sys
import os
import json
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTabWidget, QToolBar, QToolButton, 
                             QLabel, QStatusBar, QSplitter, QFrame)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QIcon, QFont, QPalette, QColor

# Import widgets
from widgets.filter_tab import FilterTab
from widgets.service_tab import ServiceTab
from widgets.lists_tab import ListsTab
from widgets.game_filter_tab import GameFilterTab
from widgets.diagnostics_tab import DiagnosticsTab
from widgets.settings_tab import SettingsTab
from widgets.domain_checker_tab import DomainCheckerTab
from widgets.backup_tab import BackupTab
from widgets.about_tab import AboutTab
from widgets.stats_tab import StatsTab

# Import utilities
from utils.config_manager import ConfigManager
from utils.file_manager import FileManager
from utils.process_manager import ProcessManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.base_dir = Path(__file__).resolve().parent.parent
        self.config_manager = ConfigManager(self.base_dir)
        self.file_manager = FileManager(str(self.base_dir))
        self.process_manager = ProcessManager()
        self.threads = []
        self.init_ui()
        self.load_theme()
        
    def init_ui(self):
        """Initialize the Dark Theme UI"""
        self.setWindowTitle("Zapret Manager v1.8.0 - Dark Theme")
        self.setMinimumSize(1200, 800)
        
        # Set Dark theme window properties
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #2d2d2d;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #505050;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: #404040;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #505050;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        # Create central widget with Dark theme layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with proper Dark theme spacing
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create Dark theme sidebar
        self.create_dark_sidebar()
        
        # Create splitter for responsive layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #404040;
            }
        """)
        
        # Add sidebar to splitter
        splitter.addWidget(self.sidebar)
        
        # Create content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(16)
        
        # Create tab widget with Dark theme styling
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        
        # Initialize tabs with Dark theme
        self.init_tabs()
        
        content_layout.addWidget(self.tab_widget)
        splitter.addWidget(content_widget)
        
        # Set splitter proportions (sidebar:content = 1:4)
        splitter.setSizes([240, 960])
        
        main_layout.addWidget(splitter)
        
        # Create Dark theme status bar
        self.create_status_bar()
        
    def create_dark_sidebar(self):
        """Create Dark theme sidebar with navigation"""
        self.sidebar = QFrame()
        self.sidebar.setObjectName("darkSidebar")
        self.sidebar.setStyleSheet("""
            #darkSidebar {
                background-color: #2d2d2d;
                border-right: 1px solid #404040;
                min-width: 240px;
                max-width: 240px;
            }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)
        sidebar_layout.setSpacing(8)
        
        # App title with Dark theme typography
        title_label = QLabel("Zapret Manager")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-size: 20px;
                font-weight: bold;
                padding: 16px 0px;
                margin-bottom: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        sidebar_layout.addWidget(title_label)
        
        # Navigation buttons with Dark theme
        self.nav_buttons = {}
        
        nav_items = [
            ("🔧", "Filter", "Основные настройки фильтрации"),
            ("⚙️", "Service", "Управление службой"),
            ("📋", "Lists", "Управление списками доменнов"),
            ("🎮", "Game Filter", "Игровой фильтр"),
            ("📊", "Stats", "Статистика"),
            ("🔍", "Diagnostics", "Диагностика системы"),
            ("🌐", "Domain Checker", "Проверка доменнов"),
            ("💾", "Backup", "Резервное копирование"),
            ("⚙️", "Settings", "Настройки приложения"),
            ("ℹ️", "About", "О программе")
        ]
        
        for icon, name, tooltip in nav_items:
            btn = QToolButton()
            btn.setText(f"{icon} {name}")
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QToolButton {
                    background-color: transparent;
                    border: none;
                    border-radius: 8px;
                    padding: 12px 16px;
                    margin: 2px 0px;
                    text-align: left;
                    color: #cccccc;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 48px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QToolButton:hover {
                    background-color: #404040;
                    color: #ffffff;
                }
                QToolButton:checked {
                    background-color: #0078d4;
                    color: #ffffff;
                }
            """)
            
            btn.clicked.connect(lambda checked, n=name: self.switch_tab(n))
            self.nav_buttons[name] = btn
            sidebar_layout.addWidget(btn)
        
        # Add spacer to push buttons to top
        sidebar_layout.addStretch()
        
        # Version info at bottom
        version_label = QLabel("v1.8.0")
        version_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 12px;
                padding: 8px 0px;
                text-align: center;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        sidebar_layout.addWidget(version_label)
        
        # Set first button as checked
        if self.nav_buttons:
            first_btn = list(self.nav_buttons.values())[0]
            first_btn.setChecked(True)
    
    def create_status_bar(self):
        """Create Dark theme status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-top: 1px solid #404040;
            }
        """)
        
        # Status indicators
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        self.update_status_label = QLabel("✅ Актуальная версия")
        self.update_status_label.setStyleSheet("""
            QLabel {
                color: #4caf50;
                font-weight: 500;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        status_bar.addWidget(self.status_label)
        status_bar.addPermanentWidget(self.update_status_label)
    
    def init_tabs(self):
        """Initialize all tabs with Material Design styling"""
        # Create tabs with proper parameters
        self.filter_tab = FilterTab(self.file_manager, self.process_manager, main_window=self)
        self.service_tab = ServiceTab(self.file_manager, self.process_manager, main_window=self)
        self.lists_tab = ListsTab(self.file_manager, main_window=self)
        self.game_filter_tab = GameFilterTab(self.file_manager, main_window=self)
        self.stats_tab = StatsTab(self.file_manager)
        self.diagnostics_tab = DiagnosticsTab(main_window=self)
        self.domain_checker_tab = DomainCheckerTab(self.file_manager, main_window=self)
        self.backup_tab = BackupTab(self.file_manager, self.config_manager, main_window=self)
        self.settings_tab = SettingsTab(self.file_manager, self.process_manager, self.config_manager, main_window=self)
        self.about_tab = AboutTab()
        
        # Add tabs to widget without visible headers
        self.tab_widget.addTab(self.filter_tab, "")
        self.tab_widget.addTab(self.service_tab, "")
        self.tab_widget.addTab(self.lists_tab, "")
        self.tab_widget.addTab(self.game_filter_tab, "")
        self.tab_widget.addTab(self.stats_tab, "")
        self.tab_widget.addTab(self.diagnostics_tab, "")
        self.tab_widget.addTab(self.domain_checker_tab, "")
        self.tab_widget.addTab(self.backup_tab, "")
        self.tab_widget.addTab(self.settings_tab, "")
        self.tab_widget.addTab(self.about_tab, "")
        
        # Hide tab bar since we use sidebar navigation
        self.tab_widget.tabBar().setVisible(False)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Set initial tab
        self.tab_widget.setCurrentIndex(0)
    
    def switch_tab(self, tab_name):
        """Switch to specified tab"""
        tab_map = {
            "Filter": 0,
            "Service": 1,
            "Lists": 2,
            "Game Filter": 3,
            "Stats": 4,
            "Diagnostics": 5,
            "Domain Checker": 6,
            "Backup": 7,
            "Settings": 8,
            "About": 9
        }
        
        if tab_name in tab_map:
            self.tab_widget.setCurrentIndex(tab_map[tab_name])
    
    def on_tab_changed(self, index):
        """Handle tab change and update navigation"""
        # Update navigation buttons
        for btn in self.nav_buttons.values():
            btn.setChecked(False)
        
        tab_names = ["Filter", "Service", "Lists", "Game Filter", "Stats", 
                    "Diagnostics", "Domain Checker", "Backup", "Settings", "About"]
        
        if 0 <= index < len(tab_names):
            tab_name = tab_names[index]
            if tab_name in self.nav_buttons:
                self.nav_buttons[tab_name].setChecked(True)
    
    def load_theme(self):
        """Load Material Design theme"""
        try:
            theme_file = os.path.join(os.path.dirname(__file__), "resources", "modern_material.qss")
            if os.path.exists(theme_file):
                with open(theme_file, 'r', encoding='utf-8') as f:
                    self.setStyleSheet(f.read())
        except Exception as e:
            print(f"Error loading theme: {e}")
    
    def on_update_error(self, error):
        """Handle update check error"""
        self.update_status_label.setText("❌ Ошибка проверки обновлений")
        self.update_status_label.setStyleSheet("""
            QLabel {
                color: #d32f2f;
                font-weight: 500;
            }
        """)
    
    def register_thread(self, thread):
        """Register a thread for proper cleanup"""
        self.threads.append(thread)
        thread.finished.connect(lambda t=thread: self.remove_thread(t))
    
    def remove_thread(self, thread):
        """Safely remove thread from list"""
        if thread in self.threads:
            self.threads.remove(thread)
    
    def closeEvent(self, event):
        """Handle application close event"""
        # Stop all threads
        for thread in self.threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(3000)  # Wait up to 3 seconds
        
        # Save configuration
        try:
            self.config_manager.save_config()
        except Exception as e:
            print(f"Error saving config: {e}")
        
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Zapret Manager")
    app.setApplicationVersion("1.8.0")
    app.setOrganizationName("Zapret Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 