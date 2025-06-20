from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QGroupBox, QCheckBox, QFrame, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from utils.config_manager import ConfigManager

class GameFilterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()

        self.setup_ui()
        self.update_status()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # --- Title ---
        title_label = QLabel("Игровой фильтр")
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        main_layout.addWidget(title_label)

        # --- Description ---
        description_label = QLabel(
            "Эта функция позволяет временно отключить фильтрацию трафика для онлайн-игр, "
            "чтобы избежать возможных проблем с подключением или задержками. "
            "После завершения игровой сессии рекомендуется снова включить фильтр."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #888;")
        main_layout.addWidget(description_label)
        
        # --- Spacer ---
        main_layout.addSpacing(20)

        # --- Control Group ---
        control_group = QGroupBox("Управление")
        control_layout = QHBoxLayout()
        control_group.setLayout(control_layout)
        control_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.status_label = QLabel()
        font = self.status_label.font()
        font.setPointSize(12)
        font.setBold(True)
        self.status_label.setFont(font)

        self.toggle_switch = QCheckBox()
        self.toggle_switch.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_switch.setStyleSheet("""
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
        self.toggle_switch.toggled.connect(self.toggle_filter)

        control_layout.addWidget(QLabel("Статус:"))
        control_layout.addWidget(self.status_label)
        control_layout.addStretch()
        control_layout.addWidget(self.toggle_switch)

        main_layout.addWidget(control_group)

    def update_status(self):
        """Обновляет UI в соответствии с состоянием фильтра."""
        is_enabled = self.config_manager.is_game_filter_enabled()
        
        # Обновляем состояние свитча, не вызывая сигнал toggled
        self.toggle_switch.blockSignals(True)
        self.toggle_switch.setChecked(is_enabled)
        self.toggle_switch.blockSignals(False)

        if is_enabled:
            self.status_label.setText("ВКЛЮЧЕН")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("ВЫКЛЮЧЕН")
            self.status_label.setStyleSheet("color: red;")

    def toggle_filter(self, checked):
        """Переключает состояние фильтра."""
        if checked:
            self.config_manager.enable_game_filter()
        else:
            self.config_manager.disable_game_filter()
        self.update_status() 