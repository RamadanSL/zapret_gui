#!/usr/bin/env python3
"""
Тестовый скрипт для проверки запуска bat-файлов
"""

import sys
import os
from pathlib import Path

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_bat_launch():
    """Тестирует запуск bat-файлов"""
    print("Тестирование запуска bat-файлов...")
    
    try:
        from utils.process_manager import ProcessManager
        from utils.file_manager import FileManager
        
        # Инициализируем менеджеры
        base_dir = os.path.dirname(__file__)
        file_manager = FileManager(base_dir)
        process_manager = ProcessManager()
        
        # Получаем список bat-файлов
        bat_files = file_manager.get_bat_files()
        print(f"Найдено {len(bat_files)} bat-файлов:")
        
        for i, bat_file in enumerate(bat_files, 1):
            filename = Path(bat_file).name
            print(f"{i}. {filename}")
            
        # Проверяем наличие general.bat
        general_bat = None
        for bat_file in bat_files:
            if Path(bat_file).name.lower() == 'general.bat':
                general_bat = bat_file
                break
                
        if general_bat:
            print(f"\nТестируем запуск {Path(general_bat).name}...")
            
            # Проверяем, не запущен ли уже процесс
            if process_manager.is_process_running("winws.exe"):
                print("Процесс winws.exe уже запущен. Останавливаем...")
                process_manager.kill_process("winws.exe")
                
            # Запускаем bat-файл
            print("Запускаем bat-файл...")
            code, stdout, stderr = process_manager.run_bat(general_bat, wait=False)
            
            if code == 0:
                print("✓ Bat-файл запущен успешно")
                
                # Ждем немного и проверяем процесс
                import time
                time.sleep(2)
                
                if process_manager.is_process_running("winws.exe"):
                    print("✓ Процесс winws.exe обнаружен")
                    
                    # Показываем информацию о процессах
                    processes = process_manager.get_winws_processes()
                    print(f"Найдено {len(processes)} процессов winws.exe:")
                    for proc in processes:
                        print(f"  PID: {proc['pid']}, Статус: {proc['status']}")
                        
                    # Останавливаем процесс
                    print("Останавливаем процесс...")
                    if process_manager.kill_process("winws.exe"):
                        print("✓ Процесс остановлен")
                    else:
                        print("✗ Не удалось остановить процесс")
                else:
                    print("✗ Процесс winws.exe не обнаружен")
            else:
                print(f"✗ Ошибка запуска: {stderr}")
        else:
            print("✗ Файл general.bat не найден")
            
        return True
        
    except Exception as e:
        print(f"✗ Ошибка тестирования: {e}")
        return False

def main():
    """Основная функция"""
    print("=== Тестирование запуска bat-файлов ===\n")
    
    if test_bat_launch():
        print("\n✓ Тестирование завершено успешно")
        return 0
    else:
        print("\n✗ Тестирование завершено с ошибками")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 