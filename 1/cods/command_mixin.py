# zadachi/cods/command_mixin.py

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Импортируем константы
from .constants import (PDF_EXTENSIONS, IMG_EXTENSIONS, PY_EXTENSIONS, WEB_EXTENSIONS,
                        DEFAULT_COMMAND_FIELDS, MAX_PATH_LENGTH)

# Импортируем утилиты для работы с файлами
from .file_utils import (
    prepare_subfolder, copy_resource, copy_folder_recursive_filtered,
    find_unique_path, generate_safe_foldername
)

# Импортируем UI для критических сообщений
from PySide6.QtWidgets import QMessageBox


class CommandMixin:
    """Миксин для управления командами."""

    def _get_command_and_subfolder(self, command_idx: int, folder_key: str) -> Tuple[Dict[str, Any], Optional[Path]]:
        """Получает команду и абсолютный путь к подпапке."""
        commands_list = self.useful_commands[folder_key] # Прямой доступ
        command = commands_list[command_idx] # Прямой доступ
        command_name = command.get('name', 'unnamed_command')
        existing_subfolder_rel = command.get('subfolder')

        subfolder_rel = prepare_subfolder( # Прямой вызов file_utils
            self.tasks_folder, command_name, existing_subfolder_rel, base_folder_key=folder_key
        )

        if subfolder_rel is None:
            command['subfolder'] = None
            QMessageBox.critical(None, "Ошибка папки", f"Не удалось создать/найти подпапку для '{command_name}'.")
            return command, None

        command['subfolder'] = subfolder_rel
        target_subfolder_abs = self.tasks_folder / subfolder_rel.replace('/', os.sep)
        return command, target_subfolder_abs

    def _process_simple_resource(self,
                                 command: Dict[str, Any], target_subfolder_abs: Path,
                                 all_copied_files_paths: List[str], kwargs: Dict[str, Any],
                                 kwarg_key: str, command_key: str, is_list: bool = False,
                                 copy_args: Optional[Dict[str, Any]] = None) -> bool:
        """Обрабатывает копирование простых ресурсов."""
        source_value = kwargs.get(kwarg_key)
        if source_value is None: return True

        if copy_args is None: copy_args = {}
        operation_succeeded = True
        sources = source_value if is_list else [source_value]

        if not isinstance(sources, list): return False

        for source in sources:
            if not source or not isinstance(source, (str, Path)): continue

            result_name, copied_paths = copy_resource( # Прямой вызов file_utils
                str(source), target_subfolder_abs, self.tasks_folder, **copy_args
            )

            if result_name:
                if result_name not in command[command_key]:
                    command[command_key].append(result_name)
                all_copied_files_paths.extend(copied_paths)
            else:
                operation_succeeded = False # Ошибка при копировании хотя бы одного

        return operation_succeeded

    def _process_py_folder(self,
                           command: Dict[str, Any], target_subfolder_abs: Path,
                           all_copied_files_paths: List[str], kwargs: Dict[str, Any]) -> bool:
        """Обрабатывает копирование Python папки."""
        py_folder_str = kwargs.get('py_folder')
        if not py_folder_str: return True

        py_folder_path = Path(py_folder_str)
        if not py_folder_path.is_dir(): return False # Источник не папка

        original_py_container_name = py_folder_path.name
        base_target_py_container_abs = target_subfolder_abs / original_py_container_name
        final_target_py_container_abs = find_unique_path(base_target_py_container_abs) # Прямой вызов file_utils

        if final_target_py_container_abs is None: return False # Не нашли имя

        final_py_container_name = final_target_py_container_abs.name
        final_target_py_container_abs.mkdir(parents=True, exist_ok=True) # Прямой вызов

        py_root_copy_success = True
        allowed_root_exts = PY_EXTENSIONS.union({'.json'})
        for item in py_folder_path.iterdir():
            if item.is_file() and item.suffix.lower() in allowed_root_exts:
                 # Прямой вызов file_utils.copy_resource
                 _, copied_paths = copy_resource(
                     str(item), final_target_py_container_abs, self.tasks_folder,
                     allowed_extensions=allowed_root_exts
                 )
                 if copied_paths: all_copied_files_paths.extend(copied_paths)
                 # Игнорируем неуспех копирования отдельного файла для общего статуса

        additional_folders = kwargs.get('additional_folders', [])
        py_filter_exts = PY_EXTENSIONS.union(WEB_EXTENSIONS)
        if isinstance(additional_folders, list):
            for add_folder_name in additional_folders:
                source_add_abs = py_folder_path / add_folder_name
                target_add_abs = final_target_py_container_abs / add_folder_name
                if source_add_abs.is_dir():
                    # Прямой вызов file_utils.copy_folder_recursive_filtered
                    copied_add = copy_folder_recursive_filtered(
                        source_add_abs, target_add_abs, self.tasks_folder, py_filter_exts
                    )
                    all_copied_files_paths.extend(copied_add)

        if any(final_target_py_container_abs.iterdir()):
            if final_py_container_name not in command['py_paths']:
                command['py_paths'].append(final_py_container_name)
        else:
             final_target_py_container_abs.rmdir() # Прямой вызов (может вызвать OSError)

        return py_root_copy_success # Считаем успехом, если не было ошибок ОС при копировании корневых

    def add_command(self, name, folder_key='root', **kwargs):
        """Добавляет команду."""
        if not name or not isinstance(folder_key, str) or not folder_key: return False, []

        if folder_key not in self.useful_commands:
             if folder_key != 'root':
                 parent_key = str(Path(folder_key).parent) if '/' in folder_key else 'root'
                 # Прямой вызов без try-except
                 if not self.add_command_folder(Path(folder_key).name, base_folder_key=parent_key):
                     return False, []
             else: self.useful_commands['root'] = []

        new_command = DEFAULT_COMMAND_FIELDS.copy()
        new_command['name'] = name
        self.useful_commands.setdefault(folder_key, []).append(new_command)
        command_idx = len(self.useful_commands[folder_key]) - 1

        # Прямой вызов без try-except
        success, copied_files = self.update_command_folders(command_idx, folder_key, **kwargs)

        # Прямой вызов save_tasks
        if not self.save_tasks():
            success = False
            # Простейший откат без try-except
            if folder_key in self.useful_commands and 0 <= command_idx < len(self.useful_commands[folder_key]):
                 if self.useful_commands[folder_key][command_idx] == new_command: # Удаляем только если это та же команда
                     self.useful_commands[folder_key].pop(command_idx)

        return success, copied_files

    def update_command_folders(self, command_idx: int, folder_key: str, **kwargs: Any) -> Tuple[bool, List[str]]:
        """Обновляет ресурсы команды."""
        all_copied_files_paths = []
        overall_success = True

        # Прямой вызов без try-except (может выбросить IndexError/KeyError)
        command, target_subfolder_abs = self._get_command_and_subfolder(command_idx, folder_key)

        if target_subfolder_abs is None: return False, [] # Ошибка подготовки папки

        for key in ['ino_paths', 'py_paths', 'pdf_paths', 'img_paths']: command.setdefault(key, [])

        overall_success &= self._process_simple_resource(
            command, target_subfolder_abs, all_copied_files_paths, kwargs,
            'ino_folder', 'ino_paths', copy_args={'is_folder': True, 'include_subdirs': True})
        overall_success &= self._process_py_folder(
            command, target_subfolder_abs, all_copied_files_paths, kwargs)
        overall_success &= self._process_simple_resource(
            command, target_subfolder_abs, all_copied_files_paths, kwargs,
            'pdf_files', 'pdf_paths', is_list=True, copy_args={'allowed_extensions': PDF_EXTENSIONS})
        overall_success &= self._process_simple_resource(
            command, target_subfolder_abs, all_copied_files_paths, kwargs,
            'img_files', 'img_paths', is_list=True, copy_args={'allowed_extensions': IMG_EXTENSIONS})

        if target_subfolder_abs.exists() and not any(target_subfolder_abs.iterdir()):
            target_subfolder_abs.rmdir() # Прямой вызов
            command['subfolder'] = None

        if not self.save_tasks(): overall_success = False # Прямой вызов
        return overall_success, all_copied_files_paths

    def add_command_folder(self, folder_name, base_folder_key='root'):
        """Добавляет логическую папку."""
        if not folder_name or '/' in folder_name or '\\' in folder_name: return False
        full_folder_key = folder_name if base_folder_key == 'root' else f"{base_folder_key}/{folder_name}"
        if base_folder_key != 'root' and base_folder_key not in self.useful_commands: return False
        if full_folder_key in self.useful_commands: return True

        folder_path_abs = self.tasks_folder / full_folder_key.replace('/', os.sep)
        folder_path_abs.mkdir(parents=True, exist_ok=True) # Прямой вызов
        self.useful_commands[full_folder_key] = []

        if self.save_tasks(): # Прямой вызов
            return True
        else: # Откат без try-except
            if full_folder_key in self.useful_commands: del self.useful_commands[full_folder_key]
            if folder_path_abs.is_dir() and not any(folder_path_abs.iterdir()):
                folder_path_abs.rmdir() # Прямой вызов
            return False

    def delete_folder(self, folder_key_to_delete):
        """Удаляет логическую папку и ее содержимое."""
        if folder_key_to_delete == 'root': return False
        if folder_key_to_delete not in self.useful_commands: return True

        folders_to_delete_keys = [k for k in self.useful_commands if
                                  k == folder_key_to_delete or k.startswith(f"{folder_key_to_delete}/")]
        errors_occurred = False
        subfolders_to_delete_abs = set()
        for key in folders_to_delete_keys:
            for command in self.useful_commands.get(key, []):
                if subfolder_rel := command.get('subfolder'):
                    subfolders_to_delete_abs.add(self.tasks_folder / subfolder_rel.replace('/', os.sep))

        for path_abs in subfolders_to_delete_abs:
            if path_abs.exists():
                 # Прямые вызовы без try-except
                 if path_abs.is_dir(): shutil.rmtree(path_abs)
                 else: path_abs.unlink()
                 # Если нет ошибки - считаем удаленным

        for key in folders_to_delete_keys:
            if key == 'root': continue
            folder_path_abs = self.tasks_folder / key.replace('/', os.sep)
            if folder_path_abs.is_dir():
                shutil.rmtree(folder_path_abs) # Прямой вызов

        for key in folders_to_delete_keys:
            if key in self.useful_commands: del self.useful_commands[key] # Прямой вызов

        if not self.save_tasks(): errors_occurred = True # Прямой вызов
        if errors_occurred: QMessageBox.warning(None, "Ошибка удаления", "Не удалось удалить папку или сохранить изменения.")
        return not errors_occurred

    def move_command(self, from_folder_key, command_idx, to_folder_key):
        """Перемещает команду."""
        if from_folder_key not in self.useful_commands or \
           not (0 <= command_idx < len(self.useful_commands[from_folder_key])): return False

        if to_folder_key not in self.useful_commands:
            parent_key = str(Path(to_folder_key).parent) if '/' in to_folder_key else 'root'
            # Прямой вызов add_command_folder
            if not self.add_command_folder(Path(to_folder_key).name, base_folder_key=parent_key): return False

        command_to_move = self.useful_commands[from_folder_key][command_idx]
        old_subfolder_rel = command_to_move.get('subfolder')
        new_subfolder_rel_for_meta = old_subfolder_rel
        physical_move_error = False

        if old_subfolder_rel:
            source_abs = self.tasks_folder / old_subfolder_rel.replace('/', os.sep)
            if source_abs.is_dir():
                if to_folder_key == 'root': dest_parent_abs = self.tasks_folder
                else: dest_parent_abs = self.tasks_folder / to_folder_key.replace('/', os.sep)
                dest_parent_abs.mkdir(parents=True, exist_ok=True) # Прямой вызов
                final_dest_abs = find_unique_path(dest_parent_abs / source_abs.name) # Прямой вызов

                if final_dest_abs and len(str(final_dest_abs)) <= MAX_PATH_LENGTH:
                    shutil.move(str(source_abs), str(final_dest_abs)) # Прямой вызов
                    new_subfolder_rel_for_meta = str(final_dest_abs.relative_to(self.tasks_folder).as_posix())
                else: physical_move_error = True # Ошибка поиска имени или длины пути
            # Игнорируем ошибки OS при move

        # Обновляем метаданные напрямую
        command_popped = self.useful_commands[from_folder_key].pop(command_idx) # Прямой pop
        command_popped['subfolder'] = new_subfolder_rel_for_meta
        self.useful_commands.setdefault(to_folder_key, []).append(command_popped)
        if not self.useful_commands[from_folder_key] and from_folder_key != 'root':
            del self.useful_commands[from_folder_key] # Прямой del

        if not self.save_tasks(): return False # Прямой вызов

        if physical_move_error: QMessageBox.warning(None, "Перемещение", "Команда перемещена, но папка с файлами не была перемещена физически.")
        return True


    def delete_command(self, folder_key, command_idx):
        """Удаляет команду и ее подпапку."""
        # Прямой доступ и удаление из списка
        command = self.useful_commands[folder_key].pop(command_idx)
        subfolder_rel = command.get('subfolder')
        command_name = command.get('name', 'Без имени')

        if subfolder_rel:
            path_abs = self.tasks_folder / subfolder_rel.replace('/', os.sep)
            if path_abs.exists():
                # Прямое удаление без try-except
                if path_abs.is_dir(): shutil.rmtree(path_abs)
                else: path_abs.unlink()

        if not self.save_tasks(): # Прямой вызов
            # Простейший откат без try-except
            self.useful_commands.setdefault(folder_key, []).insert(command_idx, command)
            QMessageBox.critical(None, "Ошибка", "Не удалось сохранить изменения после удаления команды.")
            return False
        return True

    def sort_commands(self, folder_key):
        """Сортирует команды в папке по имени."""
        if folder_key in self.useful_commands and isinstance(self.useful_commands[folder_key], list):
            self.useful_commands[folder_key].sort(key=lambda x: x.get('name', '').lower()) # Прямой вызов
            return self.save_tasks() # Прямой вызов
        return False


    def rename_command_subfolder(self, folder_key, command_idx, new_name):
        """Переименовывает команду и ее подпапку."""
        if not new_name: return False
        # Прямой доступ к команде
        command = self.useful_commands[folder_key][command_idx]
        old_subfolder_rel = command.get('subfolder')
        command['name'] = new_name # Обновляем имя в JSON

        final_new_subfolder_rel = old_subfolder_rel # По умолчанию путь не меняется

        if old_subfolder_rel:
            old_subfolder_abs = self.tasks_folder / old_subfolder_rel.replace('/', os.sep)
            if folder_key == 'root': physical_parent_abs = self.tasks_folder
            else: physical_parent_abs = self.tasks_folder / folder_key.replace('/', os.sep)
            physical_parent_abs.mkdir(parents=True, exist_ok=True) # Прямой вызов

            potential_new_name_base = generate_safe_foldername(new_name) # Прямой вызов
            new_subfolder_abs = find_unique_path(physical_parent_abs / potential_new_name_base) # Прямой вызов

            if new_subfolder_abs and len(str(new_subfolder_abs)) <= MAX_PATH_LENGTH:
                final_new_subfolder_rel = str(new_subfolder_abs.relative_to(self.tasks_folder).as_posix())
                # Переименовываем, только если папка существует и пути разные
                if old_subfolder_abs.exists() and new_subfolder_abs != old_subfolder_abs:
                    old_subfolder_abs.rename(new_subfolder_abs) # Прямой вызов
            else:
                # Не удалось найти имя или путь слишком длинный - отменяем переименование папки
                final_new_subfolder_rel = old_subfolder_rel # Оставляем старый путь в JSON
                QMessageBox.warning(None,"Ошибка имени папки", f"Не удалось переименовать папку для команды '{new_name}'. Проверьте конфликты имен или длину пути.")
                # Не возвращаем False, так как имя команды УЖЕ изменено

        # Обновляем subfolder в JSON, если он изменился (или остался старым)
        command['subfolder'] = final_new_subfolder_rel

        return self.save_tasks() # Прямой вызов save_tasks