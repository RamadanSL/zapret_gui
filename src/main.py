import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                               QHBoxLayout, QVBoxLayout, QStackedWidget, QMessageBox)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QCoreApplication, Qt

from utils.settings_manager import SettingsManager
from utils.process_manager import ServiceManager

# Import widgets
from widgets.header import Header
from widgets.navigation_bar import NavigationBar
from widgets.service_tab import ServiceTab
from widgets.filter_tab import FilterTab
from widgets.settings_tab import SettingsTab
from widgets.lists_tab import ListsTab
from widgets.game_filter_tab import GameFilterTab
from widgets.stats_tab import StatsTab
from widgets.diagnostics_tab import DiagnosticsTab
from widgets.domain_checker_tab import DomainCheckerTab
from widgets.backup_tab import BackupTab
from widgets.about_tab import AboutTab

class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.settings_manager = SettingsManager()
        self.app = app

        self.setWindowTitle("Zapret GUI")
        self.setWindowIcon(QIcon("src/resources/icon.ico")) # Assuming icon exists
        self.resize(1280, 800)
        self.setStyleSheet("background-color: #f0f2f5;")

        # Main widget and layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Navigation ---
        self.nav_bar = NavigationBar()
        self.nav_bar.setObjectName("NavigationBar") # For styling
        main_layout.addWidget(self.nav_bar)

        # --- Content Area ---
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header
        header = Header()
        header.setObjectName("Header") # For styling
        content_layout.addWidget(header)

        # Pages
        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages)

        main_layout.addLayout(content_layout)
        self.setCentralWidget(central_widget)

        # --- Add pages and nav items ---
        self.add_pages()
        
        # Connect navigation
        self.nav_bar.page_changed.connect(self.pages.setCurrentIndex)

    def add_pages(self):
        # Tuples of (icon_path, name, widget_instance)
        # Using placeholders for icons
        page_data = [
            ("src/resources/service.svg", "Служба", ServiceTab()),
            ("src/resources/filter.svg", "Фильтр", FilterTab()),
            ("src/resources/lists.svg", "Списки", ListsTab()),
            ("src/resources/game.svg", "Игровой фильтр", GameFilterTab()),
            ("src/resources/stats.svg", "Статистика", StatsTab()),
            ("src/resources/diagnostics.svg", "Диагностика", DiagnosticsTab()),
            ("src/resources/domain.svg", "Проверка доменов", DomainCheckerTab()),
            ("src/resources/settings.svg", "Настройки", SettingsTab(app=self.app)),
            ("src/resources/backup.svg", "Бэкапы", BackupTab()),
            ("src/resources/about.svg", "О программе", AboutTab())
        ]
        
        for i, (icon, name, widget) in enumerate(page_data):
            self.pages.addWidget(widget)
            self.nav_bar.add_item(icon, name, i)

def load_stylesheet():
    # Загружаем только темную тему
    path = "src/resources/modern_dark.qss"
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Main stylesheet not found at {path}")
        return ""

def main():
    # --- ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ---
    service_manager = ServiceManager()
    if not service_manager.is_admin():
        reply = QMessageBox.question(None, 'Требуются права администратора',
                                     'Для работы с системными службами приложению необходимы права администратора.\n\nПерезапустить приложение с повышенными правами?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            service_manager.relaunch_as_admin()
        sys.exit() # Закрываем текущий экземпляр в любом случае
    # ------------------------------------

    QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    
    app.setStyleSheet(load_stylesheet())

    window = MainWindow(app)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 