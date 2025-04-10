# zadachi/cods/task_manager.py

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Импортируем необходимые константы
from .constants import (
    SETTINGS_FOLDER, SETTINGS_FILE, CURRENT_VERSION,
    DEFAULT_TASK_FIELDS, DEFAULT_COMMAND_FIELDS
)
# Импортируем утилиты JSON
from .json_utils import _load_json, _save_json
# Импортируем утилиты Файлов (только нужную здесь)
from .file_utils import check_file_exists

# Импортируем Миксины
from .import_export_mixin import ImportExportMixin
from .command_mixin import CommandMixin
from .task_mixin import TaskMixin

# Импорты UI только для функции выбора папки
from PySide6.QtWidgets import QFileDialog, QMessageBox


# --- Функция определения папки задач ---
# (Остается здесь, т.к. она вызывается до создания TaskManager)
def load_or_set_tasks_folder():
    """Определяет путь к файлу tasks.json."""
    default_folder = Path.home() / "TaskManagerData"
    SETTINGS_FOLDER.mkdir(exist_ok=True) # Прямой вызов

    settings = _load_json(SETTINGS_FILE, default={}) # Прямой вызов
    tasks_folder_str = settings.get('tasks_folder')
    tasks_folder = None

    if tasks_folder_str:
        potential_folder = Path(tasks_folder_str)
        # Упрощенная проверка без try-except OSError
        if potential_folder.is_dir() and os.access(potential_folder, os.W_OK):
             tasks_folder = potential_folder
        elif potential_folder.parent.is_dir() and os.access(potential_folder.parent, os.W_OK):
             # Если самой папки нет, но родительская доступна, пытаемся создать
             potential_folder.mkdir(exist_ok=True) # Прямой вызов
             if os.access(potential_folder, os.W_OK):
                  tasks_folder = potential_folder

    while tasks_folder is None:
        QMessageBox.information(None, "Выбор папки задач", "Выберите папку для хранения данных.")
        chosen_folder_str = QFileDialog.getExistingDirectory(None, "Выберите папку", str(Path.home()))

        if chosen_folder_str:
            chosen_folder = Path(chosen_folder_str)
            # Прямые вызовы mkdir/access без try-except
            chosen_folder.mkdir(parents=True, exist_ok=True)
            if not os.access(chosen_folder, os.W_OK):
                QMessageBox.critical(None, "Ошибка прав", f"Нет прав на запись:\n{chosen_folder}")
                continue # Повторный выбор

            tasks_folder = chosen_folder
            settings['tasks_folder'] = str(tasks_folder)
            settings.setdefault('theme', 'Dark')
            if not _save_json(SETTINGS_FILE, settings): # Прямой вызов
                 QMessageBox.warning(None, "Ошибка", "Не удалось сохранить путь к папке в настройках.")
            break # Выход из цикла
        else:
            # Используем папку по умолчанию при отмене выбора
            tasks_folder = default_folder
            tasks_folder.mkdir(parents=True, exist_ok=True) # Прямой вызов
            if not os.access(tasks_folder, os.W_OK):
                msg = f"Нет прав на запись в папку по умолчанию:\n{tasks_folder}"
                QMessageBox.critical(None, "Критическая ошибка", msg)
                raise OSError(msg) # Прерываем приложение

            settings['tasks_folder'] = str(tasks_folder)
            settings.setdefault('theme', 'Dark')
            if not _save_json(SETTINGS_FILE, settings): # Прямой вызов
                 QMessageBox.warning(None, "Ошибка", "Не удалось сохранить путь к папке по умолчанию.")
            break # Выход из цикла

    return tasks_folder / "tasks.json"


# --- Основной класс TaskManager ---
class TaskManager(ImportExportMixin, CommandMixin, TaskMixin): # Наследование миксинов

    def __init__(self, tasks_file):
        """Инициализация менеджера задач."""
        self.tasks_file = Path(tasks_file)
        self.tasks_folder = self.tasks_file.parent
        self.pending_tasks = []
        self.completed_tasks = []
        self.useful_commands = {'root': []}
        self.load_tasks() # Загрузка данных при старте

    # --- Базовые методы Load/Save/Normalize/Migrate ---

    def load_tasks(self):
        """Загружает и нормализует данные из JSON файла."""
        default_data = {'version': '0.0', 'pending': [], 'completed': [], 'useful_commands': {'root': []}}
        # Прямой вызов _load_json без try-except
        data = _load_json(self.tasks_file, default=default_data)

        file_version = data.get('version', '0.0')
        # Нормализация данных (внутренние методы)
        self.pending_tasks = self._normalize_task_list(data.get('pending', []), is_completed=False)
        self.completed_tasks = self._normalize_task_list(data.get('completed', []), is_completed=True)
        loaded_commands_data = data.get('useful_commands', {'root': []})
        if isinstance(loaded_commands_data, list):
            self.useful_commands = {'root': self._normalize_commands(loaded_commands_data, 'root')}
        elif isinstance(loaded_commands_data, dict):
            self.useful_commands = self._normalize_useful_commands(loaded_commands_data)
        else:
            self.useful_commands = {'root': []}
        # Миграция данных (внутренний метод)
        self._migrate_paths()

    def save_tasks(self):
        """Сохраняет текущие данные в JSON файл."""
        data_to_save = {
            'version': CURRENT_VERSION,
            'pending': self.pending_tasks,
            'completed': self.completed_tasks,
            'useful_commands': self.useful_commands
        }
        # Прямой вызов _save_json без try-except
        return _save_json(self.tasks_file, data_to_save)

    def _normalize_task_list(self, tasks_input, is_completed):
        """Приводит список задач к стандартному формату."""
        normalized_list = []
        if not isinstance(tasks_input, list): return [] # Возвращаем пустой, если не список

        default_status = 'Выполнено' if is_completed else 'Не выполнено'
        for i, task_data in enumerate(tasks_input):
            normalized_task = {}
            if isinstance(task_data, dict): normalized_task = task_data.copy()
            elif isinstance(task_data, str): normalized_task = {'name': task_data}
            else: continue # Пропускаем неверный формат

            task_with_defaults = DEFAULT_TASK_FIELDS.copy()
            task_with_defaults.update(normalized_task)
            if 'status' not in normalized_task: task_with_defaults['status'] = default_status
            current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            task_with_defaults.setdefault('created_time', current_time_str)
            if is_completed and task_with_defaults['status'] == 'Выполнено':
                 task_with_defaults.setdefault('completed_time', current_time_str)
            else: task_with_defaults['completed_time'] = None

            subtasks_input = task_with_defaults.get('subtasks', [])
            if not isinstance(subtasks_input, list): task_with_defaults['subtasks'] = []
            else:
                normalized_subtasks = []
                for j, subtask_data in enumerate(subtasks_input):
                    if isinstance(subtask_data, dict):
                        subtask_copy = subtask_data.copy()
                        subtask_copy.setdefault('name', f'Подзадача_{j}')
                        subtask_copy.setdefault('completed', False)
                        normalized_subtasks.append(subtask_copy)
                    elif isinstance(subtask_data, str):
                        normalized_subtasks.append({'name': subtask_data, 'completed': False})
                task_with_defaults['subtasks'] = normalized_subtasks
            normalized_list.append(task_with_defaults)
        return normalized_list

    def _normalize_useful_commands(self, useful_commands_dict):
        """Нормализует словарь команд."""
        normalized_dict = {}
        if not isinstance(useful_commands_dict, dict): return {'root': []}
        for folder_key, commands_list in useful_commands_dict.items():
            if not isinstance(folder_key, str) or not folder_key: continue
            normalized_dict[folder_key] = self._normalize_commands(commands_list, folder_key)
        if 'root' not in normalized_dict: normalized_dict['root'] = []
        return normalized_dict

    def _normalize_commands(self, commands_list, folder_key='?'):
        """Нормализует список команд в одной папке."""
        if not isinstance(commands_list, list): return []
        normalized_list = []
        for i, cmd_data in enumerate(commands_list):
            normalized_cmd = {}
            if isinstance(cmd_data, dict): normalized_cmd = cmd_data.copy()
            elif isinstance(cmd_data, str): normalized_cmd = {'name': cmd_data}
            else: continue

            cmd_with_defaults = DEFAULT_COMMAND_FIELDS.copy()
            cmd_with_defaults.update(normalized_cmd)
            for key in ['ino_paths', 'py_paths', 'pdf_paths', 'img_paths']:
                if not isinstance(cmd_with_defaults.get(key), list): cmd_with_defaults[key] = []
            normalized_list.append(cmd_with_defaults)
        return normalized_list

    def _migrate_paths(self):
        """Нормализует пути в useful_commands (оставляет только имя)."""
        changed = False
        # Эта проверка нужна для старых версий файла tasks.json
        if not isinstance(self.useful_commands, dict):
            old_commands = self.useful_commands if isinstance(self.useful_commands, list) else []
            self.useful_commands = {'root': self._normalize_commands(old_commands, 'root')}
            changed = True

        for folder_key in list(self.useful_commands.keys()):
            commands = self.useful_commands[folder_key]
            if not isinstance(commands, list):
                self.useful_commands[folder_key] = []
                changed = True
                continue

            folder_changed = False
            for command in commands: # Проходим по командам в папке
                if not isinstance(command, dict): continue # Пропускаем некорректные
                cmd_copy = command.copy() # Работаем с копией для сравнения
                cmd_changed_internally = False

                # Нормализация путей к файлам/папкам ресурсов
                for key in ['ino_paths', 'py_paths', 'pdf_paths', 'img_paths']:
                    original_paths = cmd_copy.get(key, [])
                    normalized_paths = []
                    paths_modified = False
                    if isinstance(original_paths, list):
                        for path_str in original_paths:
                            if isinstance(path_str, str) and path_str:
                                # Оставляем только последнюю часть пути (имя файла/папки)
                                normalized_path = Path(path_str).name
                                normalized_paths.append(normalized_path)
                                if normalized_path != path_str: paths_modified = True
                    else:
                        normalized_paths = [] # Если было не списком, сбрасываем
                        paths_modified = True

                    if paths_modified:
                        cmd_copy[key] = normalized_paths
                        cmd_changed_internally = True

                # Если пути были изменены, обновляем оригинальный словарь команды
                if cmd_changed_internally:
                    command.update(cmd_copy)
                    folder_changed = True

            if folder_changed: changed = True # Отмечаем, что были изменения в целом

        if changed:
            self.save_tasks() # Сохраняем, если были изменения

    # --- Утилитарный метод ---
    def check_tasks_file_exists(self):
        """Проверяет существование файла tasks.json."""
        # Используем импортированную утилиту
        return check_file_exists(self.tasks_file)
