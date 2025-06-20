from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QGroupBox, QToolButton,
                              QMenu, QFrame, QGridLayout, QSplitter)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor, QAction
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import datetime
import re
from pathlib import Path

from utils.file_manager import FileManager
from utils.style_utils import StyleUtils

class StatCard(QFrame):
    """Карточка для отображения статистики."""
    
    def __init__(self, title, value, icon="", color="#1976d2", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.init_ui()
    
    def init_ui(self):
        """Инициализирует интерфейс карточки."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e1e1e1;
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Заголовок с иконкой
        title_label = QLabel(f"{self.icon} {self.title}")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #666666;
                font-weight: normal;
            }
        """)
        
        # Значение
        value_label = QLabel(self.value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18pt;
                font-weight: bold;
                color: {self.color};
            }}
        """)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Сохраняем ссылку на value_label для обновления
        self.value_label = value_label

class StatsTab(QWidget):
    """Вкладка статистики с современным дизайном."""
    
    def __init__(self, file_manager: FileManager):
        super().__init__()
        self.file_manager = file_manager
        self.log_file = self.file_manager.base_dir / "logs" / "winws.log"
        
        self.init_ui()
        
        # Подключаем сигналы
        self.refresh_btn.clicked.connect(self.update_stats)
        self.clear_btn.clicked.connect(self.clear_stats)
        
        # Таймер для автообновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(5000)  # Обновляем каждые 5 секунд
        
        # Инициализация
        self.update_stats()
        
    def init_ui(self):
        """Инициализирует пользовательский интерфейс."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Заголовок
        title_label = QLabel("📊 Статистика блокировок")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #1c1b1f;
                margin-bottom: 10px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Создаем сплиттер
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Верхняя панель с карточками статистики
        top_panel = self.create_top_panel()
        splitter.addWidget(top_panel)
        
        # Нижняя панель с графиком и последними блокировками
        bottom_panel = self.create_bottom_panel()
        splitter.addWidget(bottom_panel)
        
        # Устанавливаем соотношение размеров
        splitter.setSizes([150, 400])
        main_layout.addWidget(splitter)

    def create_top_panel(self):
        """Создает верхнюю панель с карточками статистики."""
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
        layout.setSpacing(15)
        
        # Заголовок панели
        panel_header = QLabel("📈 Общая статистика")
        panel_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1c1b1f;
                padding: 5px 0;
            }
        """)
        layout.addWidget(panel_header)
        
        # Создаем карточки статистики
        stats_layout = QGridLayout()
        stats_layout.setVerticalSpacing(15)
        stats_layout.setHorizontalSpacing(15)
        
        self.total_blocks_card = StatCard("Всего заблокировано", "0", "🚫", "#f44336")
        self.today_blocks_card = StatCard("Заблокировано сегодня", "0", "📅", "#ff9800")
        self.last_block_card = StatCard("Последняя блокировка", "никогда", "⏰", "#2196f3")
        
        stats_layout.addWidget(self.total_blocks_card, 0, 0)
        stats_layout.addWidget(self.today_blocks_card, 0, 1)
        stats_layout.addWidget(self.last_block_card, 0, 2)
        
        layout.addLayout(stats_layout)
        
        return panel

    def create_bottom_panel(self):
        """Создает нижнюю панель с графиком и последними блокировками."""
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
        layout.setSpacing(15)
        
        # Создаем сплиттер для графика и списка
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Левая панель с графиком
        graph_panel = self.create_graph_panel()
        content_splitter.addWidget(graph_panel)
        
        # Правая панель с последними блокировками
        blocks_panel = self.create_blocks_panel()
        content_splitter.addWidget(blocks_panel)
        
        # Устанавливаем соотношение размеров
        content_splitter.setSizes([600, 300])
        layout.addWidget(content_splitter)
        
        return panel

    def create_graph_panel(self):
        """Создает панель с графиком."""
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
        layout.setSpacing(15)
        
        # Заголовок графика
        graph_header = QLabel("📊 График активности")
        graph_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1c1b1f;
                padding: 5px 0;
            }
        """)
        layout.addWidget(graph_header)
        
        # Создаем график
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Настраиваем стиль графика
        self.figure.patch.set_facecolor('#f8f9fa')
        self.ax.set_facecolor('#f8f9fa')
        
        self.ax.set_title("Количество блокировок по часам", fontsize=12, fontweight='bold')
        self.ax.set_xlabel("Час", fontsize=10)
        self.ax.set_ylabel("Количество блокировок", fontsize=10)
        self.ax.grid(True, alpha=0.3)
        
        layout.addWidget(self.canvas)
        
        return panel

    def create_blocks_panel(self):
        """Создает панель с последними блокировками."""
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
        layout.setSpacing(15)
        
        # Заголовок списка блокировок
        blocks_header = QLabel("🚫 Последние блокировки")
        blocks_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1c1b1f;
                padding: 5px 0;
            }
        """)
        layout.addWidget(blocks_header)
        
        # Список последних блокировок
        self.blocks_label = QLabel("Нет данных")
        self.blocks_label.setStyleSheet("""
            QLabel {
                font-size: 10pt;
                color: #666666;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 10px;
                line-height: 1.4;
            }
        """)
        self.blocks_label.setWordWrap(True)
        layout.addWidget(self.blocks_label)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.refresh_btn = QPushButton("🔄 Обновить")
        self.refresh_btn.setStyleSheet(StyleUtils.get_button_style("secondary"))
        self.refresh_btn.setMinimumHeight(35)
        self.refresh_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        self.clear_btn = QPushButton("🗑️ Очистить")
        self.clear_btn.setStyleSheet(StyleUtils.get_button_style("danger"))
        self.clear_btn.setMinimumHeight(35)
        self.clear_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        # Создаем выпадающее меню для дополнительных действий
        self.actions_menu_btn = QToolButton()
        self.actions_menu_btn.setText("📋 Действия")
        self.actions_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_menu_btn.setStyleSheet("""
            QToolButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-weight: bold;
                font-size: 10pt;
                min-height: 35px;
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
            ("📊 Экспорт статистики", self.export_stats),
            ("📈 Показать детальную статистику", self.show_detailed_stats),
            ("⚙️ Настройки автообновления", self.settings_auto_update)
        ]
        
        for text, action in actions:
            menu_action = QAction(text, self)
            menu_action.triggered.connect(action)
            self.actions_menu.addAction(menu_action)
        
        self.actions_menu_btn.setMenu(self.actions_menu)
        
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addWidget(self.actions_menu_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        return panel
        
    def update_stats(self):
        """Обновляет статистику"""
        if not self.log_file.exists():
            self.blocks_label.setText("📁 Файл логов не найден")
            return
            
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Счетчики
            total_blocks = 0
            today_blocks = 0
            last_block_time = None
            blocks_by_hour = {i: 0 for i in range(24)}
            last_blocks = []
            
            today = datetime.date.today()
            
            for line in reversed(lines):
                if "Blocked connection" in line:
                    total_blocks += 1
                    
                    # Парсим время
                    try:
                        timestamp_str = re.search(r'\[(.*?)\]', line).group(1)
                        timestamp = datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if last_block_time is None:
                            last_block_time = timestamp
                            
                        if timestamp.date() == today:
                            today_blocks += 1
                            blocks_by_hour[timestamp.hour] += 1
                            
                        # Сохраняем последние 5 блокировок
                        if len(last_blocks) < 5:
                            # Извлекаем IP адрес
                            ip_match = re.search(r'to ([\d\.]+)', line)
                            if ip_match:
                                last_blocks.append(f"🕐 {timestamp_str}: {ip_match.group(1)}")
                                
                    except Exception:
                        continue
                        
            # Обновляем карточки статистики
            self.total_blocks_card.value_label.setText(str(total_blocks))
            self.today_blocks_card.value_label.setText(str(today_blocks))
            
            if last_block_time:
                self.last_block_card.value_label.setText(
                    last_block_time.strftime('%H:%M:%S')
                )
            else:
                self.last_block_card.value_label.setText("никогда")
                
            # Обновляем график
            self.ax.clear()
            hours = list(blocks_by_hour.keys())
            counts = list(blocks_by_hour.values())
            
            bars = self.ax.bar(hours, counts, color='#1976d2', alpha=0.8)
            self.ax.set_title("Количество блокировок по часам", fontsize=12, fontweight='bold')
            self.ax.set_xlabel("Час", fontsize=10)
            self.ax.set_ylabel("Количество блокировок", fontsize=10)
            self.ax.grid(True, alpha=0.3)
            self.ax.set_facecolor('#f8f9fa')
            
            # Добавляем значения на столбцы
            for bar, count in zip(bars, counts):
                if count > 0:
                    self.ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                               str(count), ha='center', va='bottom', fontsize=8)
            
            self.canvas.draw()
            
            # Обновляем список последних блокировок
            if last_blocks:
                self.blocks_label.setText("\n".join(last_blocks))
            else:
                self.blocks_label.setText("📊 Нет данных о блокировках")
            
        except Exception as e:
            self.blocks_label.setText(f"❌ Ошибка при обновлении статистики:\n{str(e)}")
            
    def clear_stats(self):
        """Очищает файл статистики"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self, 
            "🗑️ Очистка статистики", 
            "Вы уверены, что хотите очистить всю статистику?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.log_file.exists():
                    self.log_file.unlink()
                    
                # Создаем пустой файл
                self.log_file.parent.mkdir(parents=True, exist_ok=True)
                self.log_file.touch()
                
                self.update_stats()
                QMessageBox.information(self, "✅ Успех", "Статистика очищена!")
                
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось очистить статистику: {str(e)}")
    
    def export_stats(self):
        """Экспортирует статистику в файл."""
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "📊 Экспорт статистики", 
            f"zapret_stats_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write("=== Статистика блокировок Zapret ===\n\n")
                    f.write(f"Дата экспорта: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"Всего заблокировано: {self.total_blocks_card.value_label.text()}\n")
                    f.write(f"Заблокировано сегодня: {self.today_blocks_card.value_label.text()}\n")
                    f.write(f"Последняя блокировка: {self.last_block_card.value_label.text()}\n\n")
                    f.write("Последние блокировки:\n")
                    f.write(self.blocks_label.text())
                
                QMessageBox.information(self, "✅ Успех", f"Статистика экспортирована в {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "❌ Ошибка", f"Не удалось экспортировать статистику: {str(e)}")
    
    def show_detailed_stats(self):
        """Показывает детальную статистику."""
        from PySide6.QtWidgets import QMessageBox
        
        stats_text = f"""
📊 Детальная статистика:

🚫 Всего заблокировано: {self.total_blocks_card.value_label.text()}
📅 Заблокировано сегодня: {self.today_blocks_card.value_label.text()}
⏰ Последняя блокировка: {self.last_block_card.value_label.text()}

📈 График показывает активность блокировок по часам за сегодня.
        """
        
        QMessageBox.information(self, "📊 Детальная статистика", stats_text)
    
    def settings_auto_update(self):
        """Настройки автообновления."""
        from PySide6.QtWidgets import QMessageBox
        
        QMessageBox.information(
            self, 
            "⚙️ Настройки автообновления", 
            "Статистика обновляется автоматически каждые 5 секунд.\n"
            "Для изменения интервала используйте настройки приложения."
        )
            
    def showEvent(self, event):
        """Обработчик показа вкладки"""
        super().showEvent(event)
        self.update_stats()
        # При показе вкладки запускаем таймер
        self.timer.start()
        
    def hideEvent(self, event):
        """Обработчик скрытия вкладки"""
        super().hideEvent(event)
        # При скрытии вкладки останавливаем таймер
        self.timer.stop() 