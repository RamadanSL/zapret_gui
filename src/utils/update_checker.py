import requests
from PySide6.QtCore import QObject, Signal, QThread

class UpdateChecker(QObject):
    """Проверяет наличие обновлений на GitHub."""
    result = Signal(str, str) # new_version, url

    def __init__(self, repo="Flowseal/zapret-discord-youtube", current_version="1.7.2"):
        super().__init__()
        self.repo = repo
        self.current_version = current_version
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"

    def run(self):
        """Выполняет проверку."""
        try:
            response = requests.get(self.api_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest_version = data["tag_name"].lstrip('v')
            
            if latest_version > self.current_version:
                self.result.emit(latest_version, data["html_url"])
            else:
                self.result.emit("", "") # Нет обновлений
        except requests.RequestException:
            self.result.emit("error", "") # Ошибка сети
        except (KeyError, ValueError):
             self.result.emit("error", "") # Ошибка парсинга 