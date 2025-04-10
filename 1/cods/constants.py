# zadachi/cods/constants.py
from pathlib import Path

# --- Глобальные ---
SETTINGS_FOLDER = Path("C:/TaskManagerSettings")
SETTINGS_FILE = SETTINGS_FOLDER / "settings.json"
CURRENT_VERSION = "1.1"

# --- Задачи ---
STATUS_COLORS_DARK = {"Не выполнено": "#FF4C4C", "Выполняется": "#FFD700", "Выполнено": "#32CD32"}
STATUS_COLORS_LIGHT = {"Не выполнено": "#DC143C", "Выполняется": "#FFA500", "Выполнено": "#228B22"}
PRIORITY_LEVELS = ["Высокий", "Средний", "Низкий"]
STATUS_OPTIONS = ["Не выполнено", "Выполняется", "Выполнено"]

DEFAULT_TASK_FIELDS = {
    'name': 'Без имени', 'status': 'Не выполнено', 'priority': "Средний",
    'description': '', 'created_time': 'N/A', 'started_time': None,
    'completed_time': None, 'subtasks': []
}

# --- Команды ---
DEFAULT_COMMAND_FIELDS = {
    'name': 'Без имени', 'description': '', 'subfolder': None,
    'ino_paths': [], 'py_paths': [], 'pdf_paths': [], 'img_paths': []
}

# --- Файлы ---
INO_EXTENSIONS = {'.ino', '.cpp', '.h'}
PY_EXTENSIONS = {'.py'}
WEB_EXTENSIONS = {'.js', '.json', '.html', '.css', '.xml', '.yaml', '.yml'}
PDF_EXTENSIONS = {'.pdf'}
IMG_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp'}
EXCLUDED_DIRS = {'.git', '__pycache__', '.vscode', 'build', 'dist', 'node_modules', '.venv', 'venv'}
EXCLUDED_FILES = {'.gitignore', '.env'}
MAX_PATH_LENGTH = 260