# zadachi/cods/task_mixin.py

from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Импортируем константы, относящиеся к задачам
from .constants import PRIORITY_LEVELS, DEFAULT_TASK_FIELDS

class TaskMixin:
    """Миксин для управления задачами и подзадачами."""

    def add_task(self, name, priority="Средний"):
        """Добавляет новую задачу."""
        if not name: return False # Просто возвращаем неуспех
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Используем дефолтные поля из констант
        new_task = DEFAULT_TASK_FIELDS.copy()
        new_task.update({
            'name': name,
            'status': 'Не выполнено', # Явно ставим статус
            'created_time': current_time,
            'priority': priority
        })
        # Прямое добавление в список
        self.pending_tasks.append(new_task)
        # Прямой вызов сохранения
        return self.save_tasks()

    def add_subtask(self, task_idx, subtask_name, is_completed=False):
        """Добавляет подзадачу к существующей задаче."""
        if not subtask_name: return False
        task_list = self.completed_tasks if is_completed else self.pending_tasks
        # Прямой доступ к задаче (может вызвать IndexError)
        task = task_list[task_idx]
        # Прямое добавление подзадачи (может вызвать KeyError или TypeError)
        task.setdefault('subtasks', []).append({'name': subtask_name, 'completed': False})
        return self.save_tasks() # Прямой вызов

    def toggle_subtask(self, task_idx, subtask_original_idx, is_completed=False):
        """Переключает статус выполнения подзадачи."""
        task_list = self.completed_tasks if is_completed else self.pending_tasks
        # Прямой доступ к подзадаче (может вызвать IndexError/KeyError)
        subtask = task_list[task_idx]['subtasks'][subtask_original_idx]
        subtask['completed'] = not subtask['completed']
        return self.save_tasks() # Прямой вызов

    def change_status(self, task_idx, new_status, is_completed=False):
        """Изменяет статус задачи и перемещает между списками."""
        source_list = self.completed_tasks if is_completed else self.pending_tasks
        # Прямое удаление из списка (может вызвать IndexError)
        task = source_list.pop(task_idx)
        target_list = self.completed_tasks if new_status == "Выполнено" else self.pending_tasks

        task['status'] = new_status
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Обновление временных меток напрямую
        if new_status == "Выполняется":
            task.setdefault('started_time', current_time)
            task['completed_time'] = None # Сбрасываем время завершения
        elif new_status == "Выполнено":
            task.setdefault('started_time', task.get('created_time', current_time)) # Ставим время начала, если не было
            task.setdefault('completed_time', current_time)
        elif new_status == "Не выполнено":
            task['started_time'] = None
            task['completed_time'] = None

        target_list.append(task) # Добавляем в целевой список
        return self.save_tasks() # Прямой вызов

    def change_priority(self, task_idx, priority, is_completed=False):
        """Изменяет приоритет задачи."""
        task_list = self.completed_tasks if is_completed else self.pending_tasks
        # Прямой доступ (может вызвать IndexError)
        task_list[task_idx]['priority'] = priority
        return self.save_tasks() # Прямой вызов

    def delete_task(self, task_idx, is_completed=False):
        """Удаляет задачу."""
        task_list = self.completed_tasks if is_completed else self.pending_tasks
        # Прямое удаление (может вызвать IndexError)
        task = task_list.pop(task_idx)
        # Возвращаем статус сохранения
        return self.save_tasks() # Прямой вызов

    def sort_tasks(self, by='name'):
        """Сортирует списки задач."""
        # Используем PRIORITY_LEVELS из констант
        priority_map = {level: i for i, level in enumerate(PRIORITY_LEVELS)}
        key_func = lambda x: x.get('name', '').lower()
        reverse = False

        if by == 'created_time':
            key_func = lambda x: x.get('created_time', '0') # Сортируем как строки
            reverse = True # Новые вверху
        elif by == 'priority':
            # Несуществующий приоритет будет иметь индекс 99 (в конце)
            key_func = lambda x: priority_map.get(x.get('priority', 'Средний'), 99)
            reverse = False # Высокий (0) вверху

        # Прямая сортировка списков
        self.pending_tasks.sort(key=key_func, reverse=reverse)
        self.completed_tasks.sort(key=key_func, reverse=reverse)
        return self.save_tasks() # Прямой вызов

    def update_description(self, item_manager_idx, description, is_task=True, is_completed=False, folder_key=None):
        """Обновляет описание задачи или команды."""
        target_list = None
        if is_task:
            target_list = self.completed_tasks if is_completed else self.pending_tasks
        else:
            # Прямой доступ к useful_commands (может вызвать KeyError)
            target_list = self.useful_commands.get(folder_key or 'root')

        # Проверяем, что нашли список и индекс в пределах списка
        if isinstance(target_list, list) and 0 <= item_manager_idx < len(target_list):
             # Прямой доступ (может вызвать IndexError или KeyError, если элемент не словарь)
             target_list[item_manager_idx]['description'] = description
             return self.save_tasks() # Прямой вызов
        else:
             return False # Не нашли список или индекс неверен