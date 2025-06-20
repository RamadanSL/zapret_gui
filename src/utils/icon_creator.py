import base64
import os

def create_icon_from_base64(output_path="src/resources/icon.ico"):
    """
    Создает файл .ico из строки base64.
    Это гарантирует, что иконка будет всегда доступна при сборке
    и не потеряется как отдельный бинарный файл.
    """
    # Простая 16x16 иконка (синий квадрат) в формате base64
    ico_base64 = (
        b'AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAABILAAASCwAAAAAAAAAAAAD9/Pz//////+bm5v/9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//+fn5///////+bm5v/9/f3/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/5ubm//m5ub/n5+f/w=='
    )
    
    ico_data = base64.b64decode(ico_base64)
    
    # Создаем директорию, если она не существует
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "wb") as f:
        f.write(ico_data)
    print(f"Icon saved to {output_path}")

if __name__ == '__main__':
    create_icon_from_base64() 