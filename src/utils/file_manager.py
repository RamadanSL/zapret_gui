import os
import shutil
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

class FileManager:
    def __init__(self, base_dir: str):
        """
        Инициализация менеджера файлов
        
        Args:
            base_dir: Базовая директория проекта
        """
        self.base_dir = Path(base_dir)
        self.config_file = self.base_dir / "config.json"
        self.lists_dir = self.base_dir / "lists"
        self.bin_dir = self.base_dir / "bin"
        self.resources_dir = self.base_dir / 'src' / 'resources'
        
        # Создаем папки, если их нет
        self.lists_dir.mkdir(exist_ok=True)
        self.bin_dir.mkdir(exist_ok=True)
        self.resources_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> Dict[str, Any]:
        """Загружает конфигурацию из файла"""
        if not self.config_file.exists():
            return {}
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
            
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Сохраняет конфигурацию в файл"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False
            
    def backup_file(self, file_path: str, backup_suffix: str = ".bak") -> bool:
        """Создает резервную копию файла"""
        try:
            src = Path(file_path)
            dst = src.with_suffix(src.suffix + backup_suffix)
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
            
    def restore_file(self, backup_path: str) -> bool:
        """Восстанавливает файл из резервной копии"""
        try:
            src = Path(backup_path)
            dst = src.with_suffix("")  # Убираем .bak
            shutil.copy2(src, dst)
            return True
        except Exception:
            return False
            
    def get_bat_files(self) -> List[str]:
        """Возвращает список всех .bat файлов в корневой директории"""
        return [str(f) for f in self.base_dir.glob("*.bat")]
        
    def get_list_files(self) -> List[str]:
        """Возвращает список всех файлов в папке lists"""
        if not self.lists_dir.exists():
            return []
        return [f.name for f in self.lists_dir.iterdir() if f.is_file()]
        
    def get_list_file_path(self, filename: str) -> Optional[Path]:
        """Возвращает полный путь к файлу списка"""
        file_path = self.lists_dir / filename
        return file_path if file_path.exists() else None
        
    def read_list_file(self, filename: str) -> List[str]:
        """Читает файл со списком (один элемент на строку)"""
        try:
            file_path = self.lists_dir / filename
            if not file_path.exists():
                return []
                
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = []
                for line in f:
                    line = line.strip()
                    # Пропускаем пустые строки и комментарии
                    if line and not line.startswith('#'):
                        lines.append(line)
                return lines
        except Exception as e:
            print(f"Ошибка чтения файла {filename}: {e}")
            return []
            
    def write_list_file(self, filename: str, items: List[str]) -> bool:
        """Записывает список в файл"""
        try:
            file_path = self.lists_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                for item in items:
                    f.write(f"{item}\n")
            return True
        except Exception as e:
            print(f"Ошибка записи файла {filename}: {e}")
            return False
            
    def append_to_list_file(self, filename: str, items: List[str]) -> bool:
        """Добавляет элементы в конец файла списка"""
        try:
            file_path = self.lists_dir / filename
            with open(file_path, 'a', encoding='utf-8') as f:
                for item in items:
                    f.write(f"{item}\n")
            return True
        except Exception as e:
            print(f"Ошибка добавления в файл {filename}: {e}")
            return False
            
    def remove_from_list_file(self, filename: str, items: List[str]) -> bool:
        """Удаляет элементы из файла списка"""
        try:
            file_path = self.lists_dir / filename
            if not file_path.exists():
                return False
                
            current_items = self.read_list_file(filename)
            updated_items = [item for item in current_items if item not in items]
            
            return self.write_list_file(filename, updated_items)
        except Exception as e:
            print(f"Ошибка удаления из файла {filename}: {e}")
            return False
            
    def search_in_list_file(self, filename: str, search_term: str) -> List[str]:
        """Ищет элементы в файле списка"""
        try:
            items = self.read_list_file(filename)
            return [item for item in items if search_term.lower() in item.lower()]
        except Exception as e:
            print(f"Ошибка поиска в файле {filename}: {e}")
            return []
            
    def get_list_file_stats(self, filename: str) -> Dict[str, Any]:
        """Возвращает статистику файла списка"""
        try:
            file_path = self.lists_dir / filename
            if not file_path.exists():
                return {}
                
            items = self.read_list_file(filename)
            stats = file_path.stat()
            
            return {
                'filename': filename,
                'size_bytes': stats.st_size,
                'size_mb': round(stats.st_size / (1024 * 1024), 2),
                'lines_total': len(items),
                'modified': stats.st_mtime,
                'created': stats.st_ctime
            }
        except Exception as e:
            print(f"Ошибка получения статистики файла {filename}: {e}")
            return {}
            
    def validate_list_file(self, filename: str) -> Dict[str, Any]:
        """Проверяет валидность файла списка"""
        try:
            file_path = self.lists_dir / filename
            if not file_path.exists():
                return {'valid': False, 'error': 'Файл не найден'}
                
            items = self.read_list_file(filename)
            
            # Проверяем на дубликаты
            duplicates = []
            seen = set()
            for item in items:
                if item in seen:
                    duplicates.append(item)
                else:
                    seen.add(item)
                    
            # Проверяем на пустые элементы
            empty_items = [i for i, item in enumerate(items) if not item.strip()]
            
            return {
                'valid': True,
                'total_items': len(items),
                'unique_items': len(seen),
                'duplicates': len(duplicates),
                'duplicate_items': duplicates,
                'empty_items': len(empty_items),
                'empty_positions': empty_items
            }
        except Exception as e:
            return {'valid': False, 'error': str(e)}
            
    def merge_list_files(self, source_files: List[str], target_file: str) -> bool:
        """Объединяет несколько файлов списков в один"""
        try:
            all_items = set()
            for filename in source_files:
                items = self.read_list_file(filename)
                all_items.update(items)
                
            return self.write_list_file(target_file, list(all_items))
        except Exception as e:
            print(f"Ошибка объединения файлов: {e}")
            return False
            
    def split_list_file(self, filename: str, chunk_size: int, prefix: str = "split_") -> List[str]:
        """Разделяет большой файл списка на части"""
        try:
            items = self.read_list_file(filename)
            if not items:
                return []
                
            created_files = []
            for i in range(0, len(items), chunk_size):
                chunk = items[i:i + chunk_size]
                chunk_filename = f"{prefix}{i//chunk_size + 1}.txt"
                
                if self.write_list_file(chunk_filename, chunk):
                    created_files.append(chunk_filename)
                    
            return created_files
        except Exception as e:
            print(f"Ошибка разделения файла {filename}: {e}")
            return []

    def get_resource_path(self, resource_name):
        """Возвращает полный путь к файлу в папке resources."""
        return self.resources_dir / resource_name 