import os

class ConfigManager:
    """
    Управляет конфигурациями, основанными на файлах-флагах,
    аналогично 'game_filter.enabled' и 'ipset.enabled' в .bat скриптах.
    """
    def __init__(self, base_path="bin"):
        self.base_path = os.path.abspath(base_path)
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
            
        self.game_filter_flag = os.path.join(self.base_path, "game_filter.enabled")
        self.ipset_flag = os.path.join(self.base_path, "ipset.enabled")

    # --- Game Filter ---
    def is_game_filter_enabled(self):
        """Проверяет, включен ли игровой фильтр."""
        return os.path.exists(self.game_filter_flag)

    def enable_game_filter(self):
        """Включает игровой фильтр, создавая файл-флаг."""
        try:
            with open(self.game_filter_flag, 'w') as f:
                pass
            return True, "Игровой фильтр включен."
        except Exception as e:
            return False, f"Не удалось включить игровой фильтр: {e}"

    def disable_game_filter(self):
        """Выключает игровой фильтр, удаляя файл-флаг."""
        try:
            if self.is_game_filter_enabled():
                os.remove(self.game_filter_flag)
            return True, "Игровой фильтр выключен."
        except Exception as e:
            return False, f"Не удалось выключить игровой фильтр: {e}"

    # --- IPSet ---
    def is_ipset_enabled(self):
        """Проверяет, включен ли ipset."""
        return os.path.exists(self.ipset_flag)

    def enable_ipset(self):
        """Включает ipset, создавая файл-флаг."""
        try:
            with open(self.ipset_flag, 'w') as f:
                pass
            return True, "IPset включен."
        except Exception as e:
            return False, f"Не удалось включить ipset: {e}"

    def disable_ipset(self):
        """Выключает ipset, удаляя файл-флаг."""
        try:
            if self.is_ipset_enabled():
                os.remove(self.ipset_flag)
            return True, "IPset выключен."
        except Exception as e:
            return False, f"Не удалось выключить ipset: {e}" 