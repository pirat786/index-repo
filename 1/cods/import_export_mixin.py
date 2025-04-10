# zadachi/cods/import_export_mixin.py

import shutil
import tempfile
import zipfile
from pathlib import Path

# Используем UI для сообщений пользователю
from PySide6.QtWidgets import QMessageBox, QFileDialog


class ImportExportMixin:
    """Миксин для импорта/экспорта данных задачника."""

    def export_tasks(self, archive_path="tasks_backup.zip"):
        """Экспортирует папку задач в ZIP-архив."""
        archive_path = Path(archive_path).with_suffix(".zip")
        # Удаляем существующий архив напрямую
        archive_path.unlink(missing_ok=True)

        if not hasattr(self, 'tasks_folder') or not self.tasks_folder.is_dir():
            QMessageBox.critical(None, "Ошибка экспорта", "Папка данных задачника не найдена или недоступна.")
            return False

        # Запаковываем папку напрямую
        with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in self.tasks_folder.rglob("*"):
                if file_path.resolve() == archive_path.resolve(): continue
                is_empty_dir = file_path.is_dir() and not any(file_path.iterdir())
                if file_path.is_file() or is_empty_dir:
                    relative_path = file_path.relative_to(self.tasks_folder)
                    zipf.write(file_path, relative_path)

        QMessageBox.information(None, "Успех", f"Экспорт данных в {archive_path} завершен.")
        return True


    def import_tasks(self, path):
        """Импортирует задачи из папки или ZIP-архива, заменяя текущие данные."""
        path = Path(path)
        if not path.exists():
            QMessageBox.critical(None, "Ошибка импорта", f"Выбранный путь не найден:\n{path}")
            return False

        reply = QMessageBox.question(None, "Подтверждение импорта",
                                     "Вы уверены, что хотите импортировать данные?\n"
                                     "Текущие данные будут **ЗАМЕНЕНЫ**!",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return False

        # Выполняем импорт напрямую
        if path.is_dir():
            self._import_from_folder(path, self.tasks_folder)
        elif path.suffix.lower() == '.zip':
            self._import_from_archive(path, self.tasks_folder)
        else:
            QMessageBox.critical(None, "Ошибка импорта", f"Неподдерживаемый тип источника:\n{path}")
            return False

        # Перезагрузка данных после импорта
        if hasattr(self, 'load_tasks'):
             self.load_tasks() # Прямой вызов
             QMessageBox.information(None, "Успех", "Импорт успешно завершен.")
             return True
        else:
             QMessageBox.critical(None, "Критическая ошибка", "Импорт завершен, но не удалось перезагрузить данные.")
             return False


    def _import_from_archive(self, archive_path, target_root_folder):
        """Распаковывает архив и импортирует из временной папки."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with zipfile.ZipFile(archive_path, 'r') as archive:
                archive.extractall(temp_dir) # Прямой вызов

            temp_path = Path(temp_dir)
            tasks_json_path = temp_path / "tasks.json"
            folder_to_import = None

            if tasks_json_path.is_file():
                folder_to_import = temp_path
            else:
                for item in temp_path.iterdir():
                    if item.is_dir() and (item / "tasks.json").is_file():
                        folder_to_import = item
                        break

            if folder_to_import:
                self._import_from_folder(folder_to_import, target_root_folder) # Прямой вызов
            else:
                # Прямое возбуждение исключения, если tasks.json не найден
                raise FileNotFoundError(f"Файл 'tasks.json' не найден в архиве {archive_path}")


    def _import_from_folder(self, source_folder, target_root_folder):
        """Заменяет содержимое папки target_root_folder содержимым source_folder."""
        source_folder = Path(source_folder)
        target_root_folder = Path(target_root_folder)

        if not (source_folder / "tasks.json").is_file():
             # Прямое возбуждение исключения
             raise FileNotFoundError(f"Файл 'tasks.json' не найден в исходной папке: {source_folder}")

        # Очистка папки назначения напрямую
        if target_root_folder.exists():
             for item in target_root_folder.iterdir():
                  if item.is_dir():
                      shutil.rmtree(item) # Прямой вызов
                  else:
                      item.unlink() # Прямой вызов
        else:
             target_root_folder.mkdir(parents=True, exist_ok=True) # Прямой вызов

        # Копирование напрямую
        for item in source_folder.iterdir():
            source_item = source_folder / item.name
            dest_item = target_root_folder / item.name
            if source_item.is_dir():
                shutil.copytree(source_item, dest_item, dirs_exist_ok=True) # Прямой вызов
            elif source_item.is_file():
                shutil.copy2(source_item, dest_item) # Прямой вызов