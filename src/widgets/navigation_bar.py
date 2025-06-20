from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PySide6.QtCore import Signal, QSize, Qt
from PySide6.QtGui import QIcon

class NavigationBar(QWidget):
    # Сигнал, который будет отправляться при нажатии на кнопку навигации
    # Передаем индекс страницы, на которую нужно переключиться
    page_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QWidget {
                background-color: #34495e;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 15px;
                text-align: left;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4e6a85;
            }
            QPushButton:checked {
                background-color: #2c3e50;
                border-left: 3px solid #3498db;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)

        self.buttons = []

    def add_item(self, icon_path, text, page_index):
        button = QPushButton(f"  {text}")
        button.setIcon(QIcon(icon_path))
        button.setIconSize(QSize(24, 24))
        button.setCheckable(True)
        # Связываем клик с лямбда-функцией, которая вызовет сигнал
        button.clicked.connect(lambda: self.handle_click(page_index))
        
        self.buttons.append(button)
        self.layout().addWidget(button)
        
        # Первый добавленный элемент делаем активным по умолчанию
        if len(self.buttons) == 1:
            button.setChecked(True)

    def handle_click(self, page_index):
        # Снимаем выбор со всех кнопок
        for btn in self.buttons:
            btn.setChecked(False)
        
        # Выбираем только нажатую кнопку
        self.buttons[page_index].setChecked(True)
        
        # Отправляем сигнал о смене страницы
        self.page_changed.emit(page_index) 