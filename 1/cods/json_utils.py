# zadachi/cods/json_utils.py
import json
import os
from pathlib import Path

def _load_json(file_path, default=None):
    """Читает JSON-файл."""
    file_path = Path(file_path)
    if not file_path.exists():
        return default() if callable(default) else default if default is not None else {}

    # Прямое чтение и парсинг без try-except
    with file_path.open('r', encoding='utf-8') as f:
        content = f.read()
        if not content:
            return default() if callable(default) else default if default is not None else {}
        # json.loads выбросит исключение при ошибке парсинга
        return json.loads(content)


def _save_json(file_path, data):
    """Сохраняет данные в JSON-файл."""
    file_path = Path(file_path)
    # Прямое создание папок без try-except
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # Прямая запись без try-except (кроме TypeError при dump)
    with file_path.open('w', encoding='utf-8') as f:
        try:
            # json.dump может вызвать TypeError, если данные не сериализуемы
            json.dump(data, f, ensure_ascii=False, indent=4)
            return True # Успех, если dump не вызвал TypeError
        except TypeError:
             # QMessageBox.critical(None, "Ошибка сохранения", f"Ошибка сериализации данных в JSON для файла:\n{file_path}")
             # Вывод сообщения убран, но ошибка все равно произошла
             return False # Возвращаем неуспех
    # Ошибки ОС (права доступа, диск полон) приведут к падению программы раньше