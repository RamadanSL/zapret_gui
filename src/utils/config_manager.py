import json
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigManager:
    def __init__(self, base_dir: Path):
        self.config_path = base_dir / 'config.json'
        self.config: Dict[str, Any] = {}
        self.load_config()
        
    def load_config(self):
        """Загружает конфигурацию из файла"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                # Создаем конфигурацию по умолчанию
                self.config = {
                    "general": {
                        "language": "ru",
                        "start_minimized": False,
                        "minimize_to_tray": False
                    },
                    "paths": {
                        "lists_dir": str(self.config_path.parent / "lists"),
                        "bin_dir": str(self.config_path.parent / "bin"),
                        "log_dir": str(self.config_path.parent / "logs")
                    },
                    "logging": {
                        "enabled": True,
                        "level": "INFO"
                    },
                    "service": {
                        "autostart": False,
                        "name": "ZapretService"
                    },
                    "network": {
                        "default_ping_host": "8.8.8.8",
                        "default_ping_count": 4,
                        "default_ports": "80,443,8080"
                    }
                }
                self.save_config()
                
        except Exception as e:
            print(f"Ошибка загрузки конфигурации: {e}")
            # В случае ошибки используем конфигурацию по умолчанию
            self.config = {}
            
    def save_config(self):
        """Сохраняет текущую конфигурацию в файл."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"Ошибка сохранения файла конфигурации: {e}")

    def export_config(self, file_path):
        """Экспортирует конфигурацию в указанный файл."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            raise IOError(f"Не удалось записать в файл {file_path}: {e}")

    def import_config(self, file_path):
        """Импортирует конфигурацию из указанного файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_config = json.load(f)
            # TODO: Добавить валидацию импортируемого конфига
            self.config = new_config
            self.save_config() # Сохраняем импортированную конфигурацию как текущую
        except (IOError, json.JSONDecodeError) as e:
            raise ValueError(f"Ошибка чтения или парсинга файла {file_path}: {e}")

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Получает значение из конфигурации"""
        try:
            return self.config.get(section, {}).get(key, default)
        except Exception:
            return default
            
    def set(self, section: str, key: str, value: Any):
        """Устанавливает значение в конфигурации"""
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section][key] = value
        self.save_config()
        
    def get_section(self, section: str) -> Dict[str, Any]:
        """Получает всю секцию конфигурации"""
        return self.config.get(section, {}) 