from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class Header(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(60)
        self.setStyleSheet("background-color: #2c3e50; color: white;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        
        title = QLabel("Zapret GUI")
        font = title.font()
        font.setPointSize(18)
        font.setBold(True)
        title.setFont(font)
        
        layout.addWidget(title)
        layout.addStretch() 