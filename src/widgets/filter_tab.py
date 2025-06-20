from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class FilterTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("This is the Filter Tab. Content will be added here.")
        layout.addWidget(label)
        self.setLayout(layout) 