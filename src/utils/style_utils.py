"""
Утилиты для стилей виджетов
Предоставляет общие функции для создания стилей Dark Theme
"""

class StyleUtils:
    """Утилиты для создания стилей виджетов"""
    
    @staticmethod
    def get_button_style(button_type="default"):
        """Get button style based on type"""
        base_style = """
            QPushButton {
                padding: 10px 15px;
                border: 2px solid #404040;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11pt;
                min-width: 120px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QPushButton:hover {
                border-color: #0078d4;
                background-color: #404040;
            }
            QPushButton:pressed {
                background-color: #1e1e1e;
            }
            QPushButton:disabled {
                background-color: #1e1e1e;
                color: #666666;
                border-color: #404040;
            }
        """
        
        color_styles = {
            "success": "QPushButton { background-color: #4caf50; color: white; border-color: #4caf50; }",
            "danger": "QPushButton { background-color: #f44336; color: white; border-color: #f44336; }",
            "info": "QPushButton { background-color: #2196f3; color: white; border-color: #2196f3; }",
            "warning": "QPushButton { background-color: #ff9800; color: white; border-color: #ff9800; }",
            "primary": "QPushButton { background-color: #0078d4; color: white; border-color: #0078d4; }",
            "secondary": "QPushButton { background-color: #666666; color: white; border-color: #666666; }"
        }
        
        return base_style + color_styles.get(button_type, color_styles["secondary"])
    
    @staticmethod
    def get_group_style():
        """Get common group box style"""
        return """
            QGroupBox {
                font-weight: bold;
                margin-top: 10px;
                padding-top: 10px;
                border: 1px solid #404040;
                border-radius: 6px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
    
    @staticmethod
    def get_label_style(status_type="default"):
        """Get label style based on status type"""
        base_style = """
            font-size: 12pt;
            font-weight: bold;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #404040;
            font-family: 'Segoe UI', Arial, sans-serif;
        """
        
        status_styles = {
            "success": "background-color: #1b5e20; color: #4caf50; border-color: #4caf50;",
            "error": "background-color: #b71c1c; color: #f44336; border-color: #f44336;",
            "warning": "background-color: #e65100; color: #ff9800; border-color: #ff9800;",
            "info": "background-color: #0d47a1; color: #2196f3; border-color: #2196f3;",
            "default": "background-color: #2d2d2d; color: #ffffff; border-color: #404040;"
        }
        
        return base_style + status_styles.get(status_type, status_styles["default"])
    
    @staticmethod
    def get_status_style(status_type):
        """Get status label style based on status type"""
        styles = {
            "enabled": """
                color: #4caf50;
                font-weight: bold;
                padding: 8px;
                background-color: #1b5e20;
                border: 1px solid #4caf50;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            """,
            "disabled": """
                color: #f44336;
                font-weight: bold;
                padding: 8px;
                background-color: #b71c1c;
                border: 1px solid #f44336;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            """,
            "unknown": """
                color: #ffffff;
                font-weight: bold;
                padding: 8px;
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            """
        }
        return styles.get(status_type, styles["unknown"])
    
    @staticmethod
    def get_card_style():
        """Get common card style to avoid duplication"""
        return """
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 12px;
                margin-top: 16px;
                padding-top: 16px;
                font-weight: 600;
                font-size: 16px;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 12px;
                background-color: #2d2d2d;
                color: #ffffff;
                font-weight: 600;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
    
    @staticmethod
    def get_label_style_material(color="#ffffff", weight="500"):
        """Get common label style for Dark Theme"""
        return f"""
            QLabel {{
                color: {color};
                font-weight: {weight};
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """
    
    @staticmethod
    def get_combo_style():
        """Get common combobox style"""
        return """
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 14px;
                min-height: 20px;
                min-width: 200px;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QComboBox:focus {
                border-color: #0078d4;
                border-width: 2px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                color: #ffffff;
                selection-background-color: #0078d4;
            }
        """
    
    @staticmethod
    def get_button_style_material(button_type="secondary"):
        """Get button style based on type for Dark Theme"""
        styles = {
            "success": """
                QPushButton {
                    background-color: #4caf50;
                    color: #ffffff;
                    border: none;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #888888;
                }
            """,
            "danger": """
                QPushButton {
                    background-color: #f44336;
                    color: #ffffff;
                    border: none;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #888888;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: transparent;
                    color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #0078d4;
                    color: #ffffff;
                }
                QPushButton:disabled {
                    background-color: #2d2d2d;
                    color: #666666;
                    border-color: #404040;
                }
            """,
            "info": """
                QPushButton {
                    background-color: #2196f3;
                    color: #ffffff;
                    border: none;
                    border-radius: 20px;
                    padding: 12px 24px;
                    font-weight: 500;
                    font-size: 14px;
                    min-height: 40px;
                    min-width: 120px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
                QPushButton:hover {
                    background-color: #1976d2;
                }
                QPushButton:disabled {
                    background-color: #666666;
                    color: #888888;
                }
            """
        }
        return styles.get(button_type, styles["secondary"])
    
    @staticmethod
    def get_status_style_material(status_type):
        """Get status label style based on status type for Dark Theme"""
        colors = {
            "success": "#4caf50",
            "error": "#f44336", 
            "warning": "#ff9800",
            "info": "#2196f3"
        }
        color = colors.get(status_type, "#ffffff")
        return f"""
            QLabel {{
                color: {color};
                font-weight: 600;
                font-size: 14px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """
    
    @staticmethod
    def get_text_edit_style():
        """Get common text edit style"""
        return """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """
    
    @staticmethod
    def get_progress_bar_style():
        """Get common progress bar style"""
        return """
            QProgressBar {
                background-color: #1e1e1e;
                border: none;
                border-radius: 8px;
                text-align: center;
                color: #ffffff;
                font-weight: 500;
                height: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 8px;
            }
        """
    
    @staticmethod
    def get_table_style():
        """Get common table style"""
        return """
            QTableWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                gridline-color: #404040;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #404040;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QHeaderView::section:hover {
                background-color: #404040;
            }
        """
    
    @staticmethod
    def get_list_style():
        """Get common list style"""
        return """
            QListWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #404040;
            }
            QListWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
        """
    
    @staticmethod
    def get_checkbox_style():
        """Get common checkbox style"""
        return """
            QCheckBox {
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #404040;
                border-radius: 3px;
                background-color: #2d2d2d;
            }
            QCheckBox::indicator:checked {
                background-color: #0078d4;
                border-color: #0078d4;
            }
            QCheckBox::indicator:checked::after {
                content: "✓";
                color: #ffffff;
                font-weight: bold;
                font-size: 12px;
            }
        """
    
    @staticmethod
    def get_spinbox_style():
        """Get common spinbox style"""
        return """
            QSpinBox {
                background-color: #2d2d2d;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 6px;
                color: #ffffff;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #404040;
                border: none;
                border-radius: 2px;
                width: 16px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #505050;
            }
            QSpinBox::up-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-bottom: 4px solid #ffffff;
            }
            QSpinBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid #ffffff;
            }
        """ 