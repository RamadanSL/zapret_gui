import requests
import json

class UpdateChecker:
    """
    Проверяет наличие новых версий приложения на GitHub.
    """
    def __init__(self, current_version, repo_owner="levdmitriev", repo_name="zapret-discord-youtube-gui"):
        self.current_version = current_version
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.api_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}/releases/latest"

    def check_for_updates(self):
        """
        Запрашивает информацию о последнем релизе с GitHub.
        Возвращает (is_update_available, latest_version, release_url, error_message)
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()  # Вызовет исключение для статусов 4xx/5xx
            
            latest_release = response.json()
            latest_version = latest_release.get("tag_name", "").lstrip('v')
            release_url = latest_release.get("html_url")

            if not latest_version:
                return False, None, None, "Не удалось найти тег версии в последнем релизе."

            # Простое сравнение версий. Для более сложного (например, 1.10.0 vs 1.9.0)
            # можно использовать `packaging.version`. Пока оставим так.
            if latest_version > self.current_version:
                return True, latest_version, release_url, None
            else:
                return False, self.current_version, None, "У вас последняя версия."

        except requests.exceptions.RequestException as e:
            return False, None, None, f"Ошибка сети при проверке обновлений: {e}"
        except json.JSONDecodeError:
            return False, None, None, "Ошибка при чтении ответа от сервера GitHub."
        except Exception as e:
            return False, None, None, f"Произошла непредвиденная ошибка: {e}" 