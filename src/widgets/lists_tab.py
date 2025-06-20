from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGroupBox, QCheckBox, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from utils.config_manager import ConfigManager

class ListsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()

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