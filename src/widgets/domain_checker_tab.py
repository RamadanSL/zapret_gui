from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                              QPushButton, QLabel, QTextEdit, QProgressBar,
                              QComboBox, QSpinBox, QCheckBox, QTableWidget,
                              QTableWidgetItem, QHeaderView, QMessageBox,
                              QGroupBox, QFormLayout, QSplitter, QToolButton,
                              QMenu, QFrame, QGridLayout)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QObject
from PySide6.QtGui import QFont, QColor, QBrush, QAction
import requests
import socket
import threading
import time
from urllib.parse import urlparse
from typing import List, Dict, Tuple
import dns.resolver
from utils.file_manager import FileManager
from utils.style_utils import StyleUtils

class DomainCheckerThread(QThread):
    progress_updated = Signal(int, int)  # current, total
    result_ready = Signal(str, bool, str)  # domain, is_accessible, response_time
    status_updated = Signal(str)  # status message
    finished = Signal()
    
    def __init__(self, domains: List[str], check_type: str, timeout: int = 5):
        super().__init__()
        self.domains = domains
        self.check_type = check_type
        self.timeout = timeout
        self.is_running = True
        
    def run(self):
        total = len(self.domains)
        self.status_updated.emit(f"🔍 Начинаем проверку {total} доменов...")
        
        for i, domain in enumerate(self.domains):
            if not self.is_running:
                break
                
            try:
                self.status_updated.emit(f"🔍 Проверяем: {domain}")
                is_accessible, response_time = self.check_domain(domain)
                self.result_ready.emit(domain, is_accessible, response_time)
            except Exception as e:
                self.result_ready.emit(domain, False, f"Ошибка: {str(e)}")
                
            self.progress_updated.emit(i + 1, total)
            time.sleep(0.1)  # Небольшая задержка
            
        self.status_updated.emit("✅ Проверка завершена")
        self.finished.emit()
        
    def check_domain(self, domain: str) -> Tuple[bool, str]:
        """Проверяет доступность домена"""
        start_time = time.time()
        
        if self.check_type == "HTTP":
            return self.check_http(domain)
        elif self.check_type == "HTTPS":
            return self.check_https(domain)
        elif self.check_type == "DNS":
            return self.check_dns(domain)
        elif self.check_type == "PING":
            return self.check_ping(domain)
        else:
            return False, "Неизвестный тип проверки"
            
    def check_http(self, domain: str) -> Tuple[bool, str]:
        """Проверяет HTTP доступность"""
        try:
            start_time = time.time()
            url = f"http://{domain}" if not domain.startswith(('http://', 'https://')) else domain
            response = requests.get(url, timeout=self.timeout, allow_redirects=True)
            response_time = f"{time.time() - start_time:.2f}s"
            return response.status_code < 400, response_time
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
            
    def check_https(self, domain: str) -> Tuple[bool, str]:
        """Проверяет HTTPS доступность"""
        try:
            start_time = time.time()
            url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
            response = requests.get(url, timeout=self.timeout, allow_redirects=True)
            response_time = f"{time.time() - start_time:.2f}s"
            return response.status_code < 400, response_time
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
            
    def check_dns(self, domain: str) -> Tuple[bool, str]:
        """Проверяет DNS разрешение"""
        try:
            start_time = time.time()
            dns.resolver.resolve(domain, 'A')
            response_time = f"{time.time() - start_time:.2f}s"
            return True, response_time
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
            
    def check_ping(self, domain: str) -> Tuple[bool, str]:
        """Проверяет доступность через ping"""
        try:
            start_time = time.time()
            socket.gethostbyname(domain)
            response_time = f"{time.time() - start_time:.2f}s"
            return True, response_time
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
            
    def stop(self):
        """Останавливает проверку"""
        self.is_running = False

class DomainCheckerTab(QWidget):
    """Вкладка для проверки доступности доменов с современным дизайном."""
    
    def __init__(self, file_manager, main_window=None, parent=None):
        super().__init__(parent)
        self.file_manager = file_manager
        self.main_window = main_window
        self.results = []
        self.is_operation_in_progress = False
        
        self.worker_thread = None
        self.worker = None
        
        self.init_ui()
        
    def init_ui(self):
        """Инициализирует пользовательский интерфейс."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Заголовок
        title_label = QLabel("🌐 Проверка доступности доменов")
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
        
        # Верхняя панель с настройками
        top_panel = self.create_top_panel()
        splitter.addWidget(top_panel)
        
        # Нижняя панель с результатами
        bottom_panel = self.create_bottom_panel()
        splitter.addWidget(bottom_panel)
        
        # Устанавливаем соотношение размеров
        splitter.setSizes([200, 400])
        main_layout.addWidget(splitter)
        
        # Подключаем сигналы
        self.connect_signals()
        
        # Инициализация
        self.refresh_lists()

    def create_top_panel(self):
        """Создает верхнюю панель с настройками."""
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
        
        # Группа настроек
        settings_group = QGroupBox("⚙️ Настройки проверки")
        settings_group.setStyleSheet(StyleUtils.get_group_style())
        settings_layout = QGridLayout(settings_group)
        settings_layout.setVerticalSpacing(12)
        settings_layout.setHorizontalSpacing(15)
        
        # Выбор списка
        list_label = QLabel("📋 Список доменов:")
        list_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        
        self.list_combo = QComboBox()
        self.list_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
                min-height: 35px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                margin-right: 10px;
            }
        """)
        
        self.refresh_lists_btn = QPushButton("🔄 Обновить")
        self.refresh_lists_btn.setStyleSheet(StyleUtils.get_button_style("secondary"))
        self.refresh_lists_btn.setMinimumHeight(35)
        self.refresh_lists_btn.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        
        # Тип проверки
        type_label = QLabel("🔍 Тип проверки:")
        type_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        
        self.check_type_combo = QComboBox()
        self.check_type_combo.addItems(["HTTP", "HTTPS", "DNS", "PING"])
        self.check_type_combo.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
                min-height: 35px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666666;
                margin-right: 10px;
            }
        """)
        
        # Таймаут
        timeout_label = QLabel("⏱️ Таймаут:")
        timeout_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 30)
        self.timeout_spin.setValue(5)
        self.timeout_spin.setSuffix(" сек")
        self.timeout_spin.setStyleSheet("""
            QSpinBox {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
                min-height: 35px;
            }
        """)
        
        # Размещаем элементы
        settings_layout.addWidget(list_label, 0, 0)
        settings_layout.addWidget(self.list_combo, 0, 1)
        settings_layout.addWidget(self.refresh_lists_btn, 0, 2)
        settings_layout.addWidget(type_label, 1, 0)
        settings_layout.addWidget(self.check_type_combo, 1, 1, 1, 2)
        settings_layout.addWidget(timeout_label, 2, 0)
        settings_layout.addWidget(self.timeout_spin, 2, 1, 1, 2)
        
        # Кнопки управления
        control_group = QGroupBox("🎮 Управление")
        control_group.setStyleSheet(StyleUtils.get_group_style())
        control_layout = QHBoxLayout(control_group)
        control_layout.setSpacing(10)
        
        self.start_btn = QPushButton("▶️ Начать проверку")
        self.start_btn.setStyleSheet(StyleUtils.get_button_style("primary"))
        self.start_btn.setMinimumHeight(45)
        self.start_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        
        self.stop_btn = QPushButton("⏹️ Остановить")
        self.stop_btn.setStyleSheet(StyleUtils.get_button_style("danger"))
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        
        # Прогресс и статус
        progress_group = QGroupBox("📊 Прогресс")
        progress_group.setStyleSheet(StyleUtils.get_group_style())
        progress_layout = QVBoxLayout(progress_group)
        progress_layout.setSpacing(10)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(StyleUtils.get_progress_bar_style())
        self.progress_bar.setMinimumHeight(10)
        
        self.progress_label = QLabel("Готов к проверке")
        self.progress_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                color: #666666;
                padding: 5px;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # Добавляем все группы
        layout.addWidget(settings_group)
        layout.addWidget(control_group)
        layout.addWidget(progress_group)
        
        return panel

    def create_bottom_panel(self):
        """Создает нижнюю панель с результатами."""
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
        
        # Заголовок результатов
        results_header = QLabel("📋 Результаты проверки")
        results_header.setStyleSheet("""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #1c1b1f;
                padding: 5px 0;
            }
        """)
        layout.addWidget(results_header)
        
        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["🌐 Домен", "📊 Статус", "⏱️ Время ответа", "ℹ️ Детали"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                gridline-color: #f0f0f0;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
                font-size: 11pt;
                color: #333333;
            }
        """)
        layout.addWidget(self.results_table)
        
        # Кнопки для работы с результатами
        results_btn_layout = QHBoxLayout()
        results_btn_layout.setSpacing(10)
        
        # Создаем выпадающее меню для действий
        self.actions_menu_btn = QToolButton()
        self.actions_menu_btn.setText("📋 Действия с результатами")
        self.actions_menu_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.actions_menu_btn.setStyleSheet("""
            QToolButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 10pt;
                min-height: 40px;
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
            ("📤 Экспорт результатов", self.export_results),
            ("🗑️ Очистить результаты", self.clear_results),
            ("📊 Показать статистику", self.show_statistics)
        ]
        
        for text, action in actions:
            menu_action = QAction(text, self)
            menu_action.triggered.connect(action)
            self.actions_menu.addAction(menu_action)
        
        self.actions_menu_btn.setMenu(self.actions_menu)
        results_btn_layout.addWidget(self.actions_menu_btn)
        
        # Фильтры
        filter_label = QLabel("🔍 Фильтры:")
        filter_label.setStyleSheet("""
            QLabel {
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        
        self.filter_accessible_cb = QCheckBox("✅ Доступные")
        self.filter_inaccessible_cb = QCheckBox("❌ Недоступные")
        
        for cb in [self.filter_accessible_cb, self.filter_inaccessible_cb]:
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 10pt;
                    color: #333333;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border: 2px solid #dee2e6;
                    border-radius: 4px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #1976d2;
                    border-color: #1976d2;
                }
            """)
        
        results_btn_layout.addWidget(filter_label)
        results_btn_layout.addWidget(self.filter_accessible_cb)
        results_btn_layout.addWidget(self.filter_inaccessible_cb)
        results_btn_layout.addStretch()
        
        layout.addLayout(results_btn_layout)
        
        return panel

    def connect_signals(self):
        """Подключает сигналы к слотам."""
        self.refresh_lists_btn.clicked.connect(self.refresh_lists)
        self.start_btn.clicked.connect(self.start_checking)
        self.stop_btn.clicked.connect(self.stop_checking)
        self.filter_accessible_cb.stateChanged.connect(self.filter_results)
        self.filter_inaccessible_cb.stateChanged.connect(self.filter_results)
        
    def set_operation_mode(self, in_progress=True):
        """Устанавливает режим операции."""
        self.is_operation_in_progress = in_progress
        self.start_btn.setEnabled(not in_progress)
        self.stop_btn.setEnabled(in_progress)
        self.actions_menu_btn.setEnabled(not in_progress)
        self.list_combo.setEnabled(not in_progress)
        self.check_type_combo.setEnabled(not in_progress)
        self.timeout_spin.setEnabled(not in_progress)
        
    def refresh_lists(self):
        """Обновляет список доступных файлов"""
        self.list_combo.clear()
        
        try:
            lists_dir = self.file_manager.lists_dir
            if lists_dir.exists():
                for file_path in lists_dir.glob("*.txt"):
                    self.list_combo.addItem(file_path.name, str(file_path))
                    
        except Exception as e:
            QMessageBox.warning(self, "⚠️ Ошибка", f"Не удалось загрузить списки: {str(e)}")
            
    def start_checking(self):
        """Начинает проверку доменов"""
        if self.list_combo.count() == 0:
            QMessageBox.warning(self, "⚠️ Ошибка", "Нет доступных списков доменов")
            return
            
        try:
            # Загружаем домены из выбранного файла
            file_path = self.list_combo.currentData()
            domains = self.load_domains_from_file(file_path)
            
            if not domains:
                QMessageBox.warning(self, "⚠️ Ошибка", "Не удалось загрузить домены из файла")
                return
                
            # Очищаем предыдущие результаты
            self.clear_results()
            
            # Создаем и запускаем поток проверки
            self.worker_thread = DomainCheckerThread(
                domains,
                self.check_type_combo.currentText(),
                self.timeout_spin.value()
            )
            
            self.worker_thread.progress_updated.connect(self.update_progress)
            self.worker_thread.result_ready.connect(self.add_result)
            self.worker_thread.status_updated.connect(self.progress_label.setText)
            self.worker_thread.finished.connect(self.checking_finished)
            
            self.worker_thread.start()
            
            # Обновляем UI
            self.set_operation_mode(True)
            self.progress_bar.setMaximum(len(domains))
            self.progress_bar.setValue(0)
            self.progress_label.setText("🚀 Проверка начата...")
            
            if self.main_window:
                self.main_window.register_thread(self.worker_thread)
            
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось начать проверку: {str(e)}")
            
    def stop_checking(self):
        """Останавливает проверку доменов"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait(5000)  # Ждем максимум 5 секунд
            if self.worker_thread.isRunning():
                self.worker_thread.terminate()
                self.worker_thread.wait()
            
        self.checking_finished()
        
    def checking_finished(self):
        """Обработчик завершения проверки"""
        self.set_operation_mode(False)
        self.progress_label.setText("✅ Проверка завершена")
        
    def update_progress(self, current: int, total: int):
        """Обновляет прогресс бар"""
        self.progress_bar.setValue(current)
        self.progress_label.setText(f"🔍 Проверено: {current}/{total}")
        
    def add_result(self, domain: str, is_accessible: bool, response_time: str):
        """Добавляет результат в таблицу"""
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        
        # Домен
        domain_item = QTableWidgetItem(domain)
        domain_item.setFlags(domain_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Статус
        status_text = "✅ Доступен" if is_accessible else "❌ Недоступен"
        status_item = QTableWidgetItem(status_text)
        status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        if is_accessible:
            status_item.setBackground(QColor("#e8f5e8"))
            status_item.setForeground(QColor("#2e7d32"))
        else:
            status_item.setBackground(QColor("#ffebee"))
            status_item.setForeground(QColor("#c62828"))
            
        # Время ответа
        time_item = QTableWidgetItem(response_time)
        time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        # Детали
        details_item = QTableWidgetItem("")
        details_item.setFlags(details_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        
        self.results_table.setItem(row, 0, domain_item)
        self.results_table.setItem(row, 1, status_item)
        self.results_table.setItem(row, 2, time_item)
        self.results_table.setItem(row, 3, details_item)
        
        # Сохраняем результат
        self.results.append({
            'domain': domain,
            'accessible': is_accessible,
            'response_time': response_time
        })
        
    def load_domains_from_file(self, file_path: str) -> List[str]:
        """Загружает домены из файла"""
        domains = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Извлекаем домен из строки
                        domain = self.extract_domain(line)
                        if domain:
                            domains.append(domain)
        except Exception as e:
            print(f"Ошибка загрузки файла {file_path}: {e}")
            
        return domains
        
    def extract_domain(self, line: str) -> str:
        """Извлекает домен из строки"""
        # Убираем комментарии
        if '#' in line:
            line = line.split('#')[0].strip()
            
        # Убираем лишние символы
        line = line.strip()
        
        # Если это URL, извлекаем домен
        if line.startswith(('http://', 'https://')):
            try:
                parsed = urlparse(line)
                return parsed.netloc
            except:
                return line
        else:
            # Если это просто домен
            return line
            
    def export_results(self):
        """Экспортирует результаты в файл"""
        if not self.results:
            QMessageBox.information(self, "ℹ️ Информация", "Нет результатов для экспорта")
            return
            
        try:
            from PySide6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "📤 Сохранить результаты",
                f"domain_check_results_{int(time.time())}.csv",
                "CSV файлы (*.csv);;Текстовые файлы (*.txt)"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    if file_path.endswith('.csv'):
                        f.write("Домен,Статус,Время ответа\n")
                        for result in self.results:
                            status = "Доступен" if result['accessible'] else "Недоступен"
                            f.write(f"{result['domain']},{status},{result['response_time']}\n")
                    else:
                        for result in self.results:
                            status = "Доступен" if result['accessible'] else "Недоступен"
                            f.write(f"{result['domain']} - {status} ({result['response_time']})\n")
                            
                QMessageBox.information(self, "✅ Успех", f"Результаты сохранены в {file_path}")
                
        except Exception as e:
            QMessageBox.critical(self, "❌ Ошибка", f"Не удалось экспортировать результаты: {str(e)}")
            
    def clear_results(self):
        """Очищает результаты"""
        self.results_table.setRowCount(0)
        self.results.clear()
        
    def show_statistics(self):
        """Показывает статистику результатов"""
        if not self.results:
            QMessageBox.information(self, "ℹ️ Информация", "Нет результатов для анализа")
            return
            
        total = len(self.results)
        accessible = sum(1 for r in self.results if r['accessible'])
        inaccessible = total - accessible
        
        stats_text = f"""
📊 Статистика проверки:

🌐 Всего доменов: {total}
✅ Доступных: {accessible} ({accessible/total*100:.1f}%)
❌ Недоступных: {inaccessible} ({inaccessible/total*100:.1f}%)

⏱️ Среднее время ответа: {self.calculate_average_time():.2f}s
        """
        
        QMessageBox.information(self, "📊 Статистика", stats_text)
        
    def calculate_average_time(self) -> float:
        """Вычисляет среднее время ответа"""
        if not self.results:
            return 0.0
            
        total_time = 0
        count = 0
        
        for result in self.results:
            if result['accessible']:
                try:
                    time_str = result['response_time']
                    if 's' in time_str:
                        time_val = float(time_str.replace('s', ''))
                        total_time += time_val
                        count += 1
                except:
                    continue
                    
        return total_time / count if count > 0 else 0.0
        
    def filter_results(self):
        """Фильтрует результаты в таблице"""
        show_accessible = self.filter_accessible_cb.isChecked()
        show_inaccessible = self.filter_inaccessible_cb.isChecked()
        
        for row in range(self.results_table.rowCount()):
            status_item = self.results_table.item(row, 1)
            if status_item:
                is_accessible = "✅ Доступен" in status_item.text()
                
                if show_accessible and show_inaccessible:
                    self.results_table.setRowHidden(row, False)
                elif show_accessible and is_accessible:
                    self.results_table.setRowHidden(row, False)
                elif show_inaccessible and not is_accessible:
                    self.results_table.setRowHidden(row, False)
                else:
                    self.results_table.setRowHidden(row, True)

    def closeEvent(self, event):
        """Обработчик закрытия вкладки"""
        self.stop_checking()
        super().closeEvent(event) 