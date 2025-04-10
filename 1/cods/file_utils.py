# zadachi/cods/file_utils.py
import os
import shutil
import re
from pathlib import Path
from typing import Optional, List, Set, Tuple

# Импортируем необходимые константы
from .constants import EXCLUDED_DIRS, EXCLUDED_FILES, MAX_PATH_LENGTH

def generate_safe_foldername(name: str) -> str:
    """Генерирует 'безопасное' имя для папки."""
    if not isinstance(name, str): name = str(name)
    safe_name = re.sub(r'[^\w\-\u0400-\u04FF]+', '_', name, flags=re.UNICODE)
    safe_name = safe_name.strip('_-')
    if not safe_name: safe_name = "unnamed_folder"
    return safe_name[:50]

def find_unique_path(base_target_path: Path) -> Optional[Path]:
    """Находит уникальный путь, добавляя _1, _2 и т.д."""
    if not base_target_path.exists(): return base_target_path
    parent_dir = base_target_path.parent
    original_stem = base_target_path.stem
    suffix = base_target_path.suffix
    counter = 1
    while counter <= 100:
        new_name = f"{original_stem}_{counter}{suffix}"
        new_path = parent_dir / new_name
        if not new_path.exists(): return new_path
        counter += 1
    return None # Не удалось найти уникальное имя

def copy_folder_recursive_filtered(source_dir: Path, target_dir: Path,
                                   tasks_folder_root: Path,
                                   allowed_extensions: Optional[Set[str]] = None) -> List[str]:
    """Рекурсивно копирует папку с фильтрами."""
    copied_files_rel_paths = []
    if not source_dir.is_dir(): return []

    target_dir.mkdir(parents=True, exist_ok=True) # Прямой вызов
    for root, dirs, files in os.walk(str(source_dir), topdown=True):
        current_source_dir = Path(root)
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        files[:] = [f for f in files if f not in EXCLUDED_FILES]
        relative_dir_path = current_source_dir.relative_to(source_dir)
        current_target_dir = target_dir / relative_dir_path

        for dir_name in dirs:
            (current_target_dir / dir_name).mkdir(exist_ok=True) # Прямой вызов

        for file_name in files:
            source_file = current_source_dir / file_name
            target_file = current_target_dir / file_name
            should_copy = allowed_extensions is None or source_file.suffix.lower() in allowed_extensions

            if should_copy and len(str(target_file)) <= MAX_PATH_LENGTH:
                target_file.parent.mkdir(parents=True, exist_ok=True) # Прямой вызов
                shutil.copy2(source_file, target_file) # Прямой вызов
                relative_file_path = target_file.relative_to(tasks_folder_root)
                copied_files_rel_paths.append(str(relative_file_path.as_posix()))
            # else: Ошибки длины пути или расширения просто игнорируются

    return copied_files_rel_paths

def copy_resource(source_path_str: str, target_subfolder: Path, tasks_folder_root: Path,
                  is_folder: bool = False, allowed_extensions: Optional[Set[str]] = None,
                  include_subdirs: bool = False, recursive_filter: bool = False) -> Tuple[Optional[str], List[str]]:
    """Копирует один ресурс (файл или папку)."""
    source_path = Path(source_path_str)
    copied_files_rel_paths = []

    if not source_path.exists() or \
       (is_folder and not source_path.is_dir()) or \
       (not is_folder and not source_path.is_file()):
        return None, [] # Не найден или неверный тип

    target_subfolder.mkdir(parents=True, exist_ok=True) # Прямой вызов
    target_resource_abs = find_unique_path(target_subfolder / source_path.name)
    if target_resource_abs is None: return None, [] # Не удалось найти имя
    if len(str(target_resource_abs)) > MAX_PATH_LENGTH: return None, [] # Слишком длинный путь

    final_resource_name = target_resource_abs.name
    if is_folder:
        if recursive_filter:
            copied_files_rel_paths = copy_folder_recursive_filtered(
                source_path, target_resource_abs, tasks_folder_root, allowed_extensions
            )
        else:
            target_resource_abs.mkdir() # Прямой вызов
            for src_item in source_path.iterdir():
                dst_item = target_resource_abs / src_item.name
                if len(str(dst_item)) > MAX_PATH_LENGTH: continue

                if src_item.is_file():
                    if allowed_extensions is None or src_item.suffix.lower() in allowed_extensions:
                        shutil.copy2(src_item, dst_item) # Прямой вызов
                        relative_file_path = dst_item.relative_to(tasks_folder_root)
                        copied_files_rel_paths.append(str(relative_file_path.as_posix()))
                elif src_item.is_dir() and include_subdirs:
                    shutil.copytree(src_item, dst_item, dirs_exist_ok=True) # Прямой вызов
                    for root, _, files in os.walk(str(dst_item)):
                        for file in files:
                            file_abs = Path(root) / file
                            relative_file_path = file_abs.relative_to(tasks_folder_root)
                            copied_files_rel_paths.append(str(relative_file_path.as_posix()))
    else: # Файл
        if allowed_extensions and source_path.suffix.lower() not in allowed_extensions:
            return None, [] # Неподходящее расширение
        shutil.copy2(source_path, target_resource_abs) # Прямой вызов
        relative_file_path = target_resource_abs.relative_to(tasks_folder_root)
        copied_files_rel_paths.append(str(relative_file_path.as_posix()))

    return final_resource_name, copied_files_rel_paths

def prepare_subfolder(tasks_folder_root: Path, command_name: str,
                        existing_subfolder_rel: Optional[str] = None,
                        base_folder_key: str = 'root') -> Optional[str]:
    """Готовит (создает) подпапку для команды."""
    if base_folder_key == 'root':
        physical_parent_folder_abs = tasks_folder_root
    else:
        physical_parent_folder_abs = tasks_folder_root / base_folder_key.replace('/', os.sep)

    physical_parent_folder_abs.mkdir(parents=True, exist_ok=True) # Прямой вызов

    if existing_subfolder_rel:
        potential_subfolder_abs = tasks_folder_root / existing_subfolder_rel.replace('/', os.sep)
        if potential_subfolder_abs.is_dir():
            return str(Path(existing_subfolder_rel).as_posix())

    safe_name_base = generate_safe_foldername(command_name)
    base_target_path = physical_parent_folder_abs / safe_name_base
    final_subfolder_abs = find_unique_path(base_target_path)
    if final_subfolder_abs is None: return None # Не нашли имя

    final_subfolder_abs.mkdir(parents=True, exist_ok=True) # Прямой вызов
    relative_path = final_subfolder_abs.relative_to(tasks_folder_root)
    return str(relative_path.as_posix())

def check_file_exists(file_path: Path) -> bool:
    """Проверяет существование файла."""
    # Прямой вызов без try-except OSError
    return file_path.is_file()