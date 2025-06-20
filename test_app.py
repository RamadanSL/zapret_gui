#!/usr/bin/env python3
"""
Тестовый файл для проверки всех функций Zapret Manager GUI
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from src.main import MainWindow

def test_application():
    """Тестирует запуск приложения"""
    print("Запуск тестирования Zapret Manager GUI...")
    
    # Проверяем наличие необходимых файлов
    required_files = [
        'src/main.py',
        'src/widgets/filter_tab.py',
        'src/widgets/game_filter_tab.py',
        'src/widgets/lists_tab.py',
        'src/widgets/backup_tab.py',
        'src/widgets/settings_tab.py',
        'src/widgets/service_tab.py',
        'src/widgets/stats_tab.py',
        'src/widgets/network_tab.py',
        'src/widgets/about_tab.py',
        'src/widgets/domain_checker_tab.py',
        'src/utils/config_manager.py',
        'src/utils/file_manager.py',
        'src/utils/process_manager.py'
    ]
    
    print("\nПроверка файлов:")
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - НЕ НАЙДЕН!")
    
    # Проверяем наличие .bat файлов
    bat_files = [
        'discord.bat',
        'general.bat',
        'service.bat',
        'start.bat'
    ]
    
    print("\nПроверка .bat файлов:")
    for bat_file in bat_files:
        if os.path.exists(bat_file):
            print(f"✓ {bat_file}")
        else:
            print(f"✗ {bat_file} - НЕ НАЙДЕН!")
    
    # Проверяем папки
    folders = [
        'bin',
        'lists',
        'src',
        'src/widgets',
        'src/utils'
    ]
    
    print("\nПроверка папок:")
    for folder in folders:
        if os.path.exists(folder):
            print(f"✓ {folder}/")
        else:
            print(f"✗ {folder}/ - НЕ НАЙДЕНА!")
    
    print("\nЗапуск приложения...")
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        print("✓ Приложение успешно запущено!")
        print("✓ Все вкладки загружены:")
        
        # Проверяем вкладки
        tabs = [
            "Управление фильтром",
            "Game Filter", 
            "Списки",
            "Бэкап",
            "Проверка доменов",
            "Настройки",
            "Служба",
            "Статистика",
            "Сеть",
            "О программе"
        ]
        
        for i, tab_name in enumerate(tabs):
            if i < window.tabs.count():
                actual_name = window.tabs.tabText(i)
                if actual_name == tab_name:
                    print(f"  ✓ {tab_name}")
                else:
                    print(f"  ✗ {tab_name} (найдено: {actual_name})")
            else:
                print(f"  ✗ {tab_name} - НЕ НАЙДЕНА!")
        
        print("\nПриложение готово к использованию!")
        print("Закройте окно приложения для завершения теста.")
        
        return app.exec()
        
    except Exception as e:
        print(f"✗ Ошибка при запуске: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(test_application()) 