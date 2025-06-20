from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, 
                               QLabel, QApplication)
from PySide6.QtCore import Qt

class SettingsTab(QWidget):
    def __init__(self, app: QApplication, parent=None):
        super().__init__(parent)
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Placeholder ---
        info_label = QLabel("Раздел настроек находится в разработке.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        main_layout.addWidget(info_label)
        main_layout.addStretch() 