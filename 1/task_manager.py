# task_manager.py
import os
import json
import logging
import shutil
from datetime import datetime
from PySide6.QtWidgets import QFileDialog

# Фиксированная папка для настроек
SETTINGS_FOLDER = "C:/TaskManagerSettings"
SETTINGS_FILE = os.path.abspath(os.path.join(SETTINGS_FOLDER, "settings.json"))

# Настройка логирования
logging.basicConfig(level=logging.INFO)

def load_or_set_tasks_folder():
    """Загружает или устанавливает TASKS_FOLDER и возвращает TASKS_FILE"""
    default_folder = "C:/tasks"
    tasks_folder = None

    try:
        os.makedirs(SETTINGS_FOLDER, exist_ok=True)
        logging.info(f"Папка {SETTINGS_FOLDER} создана или уже существует")
    except Exception as e:
        logging.error(f"Не удалось создать {SETTINGS_FOLDER}: {e}")
        tasks_folder = os.path.expanduser("~")  # Используем домашнюю папку пользователя как запасной вариант
        settings_file = os.path.abspath(os.path.join(tasks_folder, "settings.json"))
    else:
        settings_file = SETTINGS_FILE

    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                tasks_folder = settings.get('tasks_folder', default_folder)
                logging.info(f"Загружена папка задач из {settings_file}: {tasks_folder}")
                if not os.path.exists(tasks_folder):
                    logging.warning(f"Папка {tasks_folder} не существует, используется значение по умолчанию: {default_folder}")
                    tasks_folder = default_folder
        except json.JSONDecodeError as e:
            logging.error(f"Ошибка парсинга JSON в {settings_file}: {e}")
            tasks_folder = default_folder
        except Exception as e:
            logging.error(f"Ошибка загрузки {settings_file}: {e}")
            tasks_folder = default_folder
    else:
        tasks_folder = QFileDialog.getExistingDirectory(None,
                                                        "Выберите папку для хранения задач (выбор будет сохранён)",
                                                        default_folder)
        if not tasks_folder:
            tasks_folder = default_folder
        try:
            os.makedirs(tasks_folder, exist_ok=True)
            logging.info(f"Создаём новую папку задач: {tasks_folder}")
            settings = {'tasks_folder': tasks_folder, 'theme': 'Dark'}
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            logging.info(f"Настройки сохранены в {settings_file}")
        except Exception as e:
            logging.error(f"Не удалось создать папку или settings.json: {e}")
            tasks_folder = os.path.expanduser("~")

    tasks_file = os.path.abspath(os.path.join(tasks_folder, "tasks.json"))
    logging.info(f"Возвращён tasks_file: {tasks_file}")
    return tasks_file

class TaskManager:
    STATUS_COLORS_DARK = {"Не выполнено": "#FF0000", "Выполняется": "#FFFF00", "Выполнено": "#008000"}
    STATUS_COLORS_LIGHT = {"Не выполнено": "#FF0000", "Выполняется": "#DAA520", "Выполнено": "#008000"}
    PRIORITY_LEVELS = ["Высокий", "Средний", "Низкий"]
    STATUS_OPTIONS = ["Не выполнено", "Выполняется", "Выполнено"]
    DEFAULT_FIELDS = {
        'created_time': 'N/A', 'started_time': None, 'completed_time': None, 'priority': "Средний"
    }

    def __init__(self, tasks_file):
        self.tasks_file = tasks_file
        self.pending_tasks = []
        self.completed_tasks = []
        self.useful_commands = []
        self.load_tasks()

    def load_tasks(self):
        try:
            if os.path.exists(self.tasks_file):
                with open(self.tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pending_tasks = data.get('pending', [])
                    self.completed_tasks = data.get('completed', [])
                    self.useful_commands = data.get('useful_commands', [])
                    self._normalize_tasks()
            else:
                self.save_tasks()
        except Exception as e:
            logging.error(f"Ошибка загрузки {self.tasks_file}: {e}")
            self.pending_tasks = []
            self.completed_tasks = []
            self.useful_commands = []
            self.save_tasks()

    def _normalize_tasks(self):
        for task_list in [self.pending_tasks, self.completed_tasks]:
            for task in task_list:
                task.update({k: v for k, v in self.DEFAULT_FIELDS.items() if k not in task})
        for command in self.useful_commands:
            if 'ino_path' not in command:
                command['ino_path'] = None
            if 'subfolder' not in command:
                command['subfolder'] = None
        self.save_tasks()

    def save_tasks(self):
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'pending': self.pending_tasks,
                    'completed': self.completed_tasks,
                    'useful_commands': self.useful_commands
                }, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Ошибка сохранения {self.tasks_file}: {e}")

    def add_task(self, name, priority="Средний"):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.pending_tasks.append({
            'name': name, 'status': 'Не выполнено', 'description': '',
            'created_time': current_time, 'started_time': None, 'completed_time': None,
            'priority': priority
        })
        self.save_tasks()

    def add_command(self, name, ino_path=None, folder_path=None, additional_folders=None):
        new_ino_path = None
        subfolder = None
        if ino_path or folder_path:
            subfolder = self._create_unique_subfolder(name)
            if ino_path and os.path.exists(ino_path):
                new_ino_path = self._copy_ino_file(ino_path, subfolder)
            elif folder_path and os.path.exists(folder_path):
                new_ino_path = self._copy_py_files_from_folder(folder_path, subfolder, additional_folders)
        self.useful_commands.append({
            'name': name,
            'description': '',
            'ino_path': new_ino_path,
            'subfolder': subfolder
        })
        self.save_tasks()

    def _create_unique_subfolder(self, name):
        base_name = ''.join(c for c in name if c.isalnum() or c in ('_', '-'))[:50]
        subfolder = base_name
        counter = 1
        tasks_folder = os.path.dirname(self.tasks_file)
        while os.path.exists(os.path.join(tasks_folder, subfolder)):
            subfolder = f"{base_name}_{counter}"
            counter += 1
        os.makedirs(os.path.join(tasks_folder, subfolder))
        return subfolder

    def _copy_ino_file(self, source_path, subfolder):
        filename = os.path.basename(source_path)
        base, ext = os.path.splitext(filename)
        tasks_folder = os.path.dirname(self.tasks_file)
        target_path = os.path.join(tasks_folder, subfolder, filename)
        counter = 1
        while os.path.exists(target_path):
            target_path = os.path.join(tasks_folder, subfolder, f"{base}_{counter}{ext}")
            counter += 1
        try:
            shutil.copy2(source_path, target_path)
            return os.path.basename(target_path)
        except Exception as e:
            logging.error(f"Ошибка копирования .ino файла: {e}")
            return None

    def _copy_py_files_from_folder(self, folder_path, subfolder, additional_folders=None):
        py_files = []
        tasks_folder = os.path.dirname(self.tasks_file)
        files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
        for file in files:
            if file.endswith('.py'):
                source_path = os.path.join(folder_path, file)
                base, ext = os.path.splitext(file)
                target_path = os.path.join(tasks_folder, subfolder, file)
                counter = 1
                while os.path.exists(target_path):
                    target_path = os.path.join(tasks_folder, subfolder, f"{base}_{counter}{ext}")
                    counter += 1
                try:
                    shutil.copy2(source_path, target_path)
                    py_files.append(os.path.basename(target_path))
                except Exception as e:
                    logging.error(f"Ошибка копирования .py файла {file}: {e}")

        if additional_folders:
            for folder_name in additional_folders:
                source_special_path = os.path.join(folder_path, folder_name)
                if os.path.exists(source_special_path) and os.path.isdir(source_special_path):
                    target_special_path = os.path.join(tasks_folder, subfolder, folder_name)
                    try:
                        shutil.copytree(source_special_path, target_special_path, dirs_exist_ok=True)
                        for root, _, files in os.walk(target_special_path):
                            for file in files:
                                if file.endswith('.py'):
                                    rel_path = os.path.relpath(os.path.join(root, file),
                                                               os.path.join(tasks_folder, subfolder))
                                    py_files.append(rel_path)
                    except Exception as e:
                        logging.error(f"Ошибка копирования папки {folder_name}: {e}")

        return py_files if py_files else None

    def export_tasks(self, folder_path):
        try:
            os.makedirs(folder_path, exist_ok=True)
            with open(os.path.join(folder_path, "tasks.json"), 'w', encoding='utf-8') as f:
                json.dump({
                    'pending': self.pending_tasks,
                    'completed': self.completed_tasks,
                    'useful_commands': self.useful_commands
                }, f, ensure_ascii=False, indent=4)

            tasks_folder = os.path.dirname(self.tasks_file)
            for command in self.useful_commands:
                subfolder = command.get('subfolder')
                if subfolder:
                    source_subfolder = os.path.join(tasks_folder, subfolder)
                    target_subfolder = os.path.join(folder_path, subfolder)
                    if os.path.exists(source_subfolder):
                        shutil.copytree(source_subfolder, target_subfolder, dirs_exist_ok=True)
                    else:
                        logging.warning(f"Подкаталог {source_subfolder} не существует, пропускаем копирование.")
            return True
        except Exception as e:
            logging.error(f"Ошибка экспорта: {e}")
            return False

    def import_tasks(self, folder_path):
        try:
            tasks_file = os.path.join(folder_path, "tasks.json")
            if not os.path.exists(tasks_file):
                raise FileNotFoundError("tasks.json не найден в указанной папке")

            tasks_folder = os.path.dirname(self.tasks_file)
            for item in os.listdir(tasks_folder):
                item_path = os.path.join(tasks_folder, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif item.endswith(('.ino', '.py')):
                    os.remove(item_path)

            with open(tasks_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.pending_tasks = data.get('pending', [])
                self.completed_tasks = data.get('completed', [])
                self.useful_commands = data.get('useful_commands', [])

            for command in self.useful_commands:
                if command.get('subfolder'):
                    source_subfolder = os.path.join(folder_path, command['subfolder'])
                    target_subfolder = os.path.join(tasks_folder, command['subfolder'])
                    if os.path.exists(source_subfolder):
                        shutil.copytree(source_subfolder, target_subfolder, dirs_exist_ok=True)
                    else:
                        logging.warning(f"Подкаталог {source_subfolder} не найден при импорте.")

            self._normalize_tasks()
            return True
        except Exception as e:
            logging.error(f"Ошибка импорта: {e}")
            return False

    def update_command_ino(self, idx, ino_path=None, folder_path=None, additional_folders=None):
        if 0 <= idx < len(self.useful_commands):
            new_ino_path = None
            subfolder = self.useful_commands[idx].get('subfolder')
            if not subfolder:
                subfolder = self._create_unique_subfolder(self.useful_commands[idx]['name'])
                self.useful_commands[idx]['subfolder'] = subfolder
            if ino_path and os.path.exists(ino_path):
                new_ino_path = self._copy_ino_file(ino_path, subfolder)
            elif folder_path and os.path.exists(folder_path):
                new_ino_path = self._copy_py_files_from_folder(folder_path, subfolder, additional_folders)
            self.useful_commands[idx]['ino_path'] = new_ino_path
            self.save_tasks()

    def change_status(self, task_idx, new_status, is_completed=False):
        source_list = self.completed_tasks if is_completed else self.pending_tasks
        target_list = self.pending_tasks if new_status != "Выполнено" else self.completed_tasks
        if 0 <= task_idx < len(source_list):
            task = source_list.pop(task_idx)
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if new_status == "Выполняется" and task['started_time'] is None:
                task['started_time'] = current_time
            elif new_status == "Выполнено" and task['completed_time'] is None:
                task['completed_time'] = current_time
            task['status'] = new_status
            target_list.append(task)
            self.save_tasks()

    def change_priority(self, task_idx, priority, is_completed=False):
        task_list = self.completed_tasks if is_completed else self.pending_tasks
        if 0 <= task_idx < len(task_list):
            task_list[task_idx]['priority'] = priority
            self.save_tasks()

    def delete_task(self, task_idx, is_completed=False):
        task_list = self.completed_tasks if is_completed else self.pending_tasks
        if 0 <= task_idx < len(task_list):
            task_list.pop(task_idx)
            self.save_tasks()

    def delete_command(self, command_idx):
        if 0 <= command_idx < len(self.useful_commands):
            subfolder = self.useful_commands[command_idx].get('subfolder')
            tasks_folder = os.path.dirname(self.tasks_file)
            if subfolder and os.path.exists(os.path.join(tasks_folder, subfolder)):
                shutil.rmtree(os.path.join(tasks_folder, subfolder))
            self.useful_commands.pop(command_idx)
            self.save_tasks()

    def sort_tasks(self, by='name'):
        sort_key = {
            'name': lambda x: x['name'].lower(),
            'created_time': lambda x: x['created_time'] if x['created_time'] != 'N/A' else '',
            'priority': lambda x: self.PRIORITY_LEVELS.index(x['priority'])
        }.get(by, lambda x: x['name'].lower())
        self.pending_tasks.sort(key=sort_key, reverse=(by == 'created_time'))
        self.completed_tasks.sort(key=sort_key, reverse=(by == 'created_time'))
        self.save_tasks()

    def sort_commands(self):
        self.useful_commands.sort(key=lambda x: x['name'].lower())
        self.save_tasks()

    def update_description(self, idx, description, is_task=True, is_completed=False):
        target_list = (self.completed_tasks if is_completed else self.pending_tasks) if is_task else self.useful_commands
        if 0 <= idx < len(target_list):
            target_list[idx]['description'] = description
            self.save_tasks()

    def check_tasks_file_exists(self):
        """Проверяет наличие файла tasks.json"""
        return os.path.exists(self.tasks_file)