import json
import os

class SettingsManager:
    """
    Управляет настройками приложения, сохраняя их в config.json.
    """
    def __init__(self, config_path="config.json"):
        self.config_path = os.path.abspath(config_path)
        self.settings = self.load_settings()

    def load_settings(self):
        """Загружает настройки из файла. Если файл не найден, возвращает дефолтные."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self.get_default_settings()
        except (json.JSONDecodeError, IOError):
            return self.get_default_settings()

    def save_settings(self):
        """Сохраняет текущие настройки в файл."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
            return True, "Настройки сохранены."
        except IOError as e:
            return False, f"Не удалось сохранить настройки: {e}"

    def get_setting(self, key, default=None):
        """Получает значение настройки по ключу."""
        return self.settings.get(key, default)

    def set_setting(self, key, value):
        """Устанавливает значение настройки и сохраняет его."""
        self.settings[key] = value
        self.save_settings()

    def get_default_settings(self):
        """Возвращает словарь с настройками по умолчанию."""
        return {
            "theme": "dark",
            "autostart_app": False
        } 