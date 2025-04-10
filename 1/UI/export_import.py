import logging
from pathlib import Path
from . import QFileDialog, QMessageBox

class ExportImportMixin:
    def export_tasks(self):
        """
        Обрабатывает экспорт задач в ZIP-архив.
        Запрашивает у пользователя имя файла для сохранения.
        """
        default_filename = "tasks_backup.zip"
        archive_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт задач в ZIP-архив",
            default_filename,
            "ZIP Archives (*.zip);;All Files (*)"
        )

        if archive_path:
            if not archive_path.lower().endswith(".zip"):
                archive_path += ".zip"
            success = self.task_manager.export_tasks(archive_path)
            if success:
                QMessageBox.information(self, "Успех", f"Задачи успешно экспортированы в:\n{archive_path}")
            else:
                QMessageBox.warning(self, "Ошибка экспорта", "Не удалось экспортировать задачи. Проверьте лог для деталей.")
        self._hide_settings_panel()

    def import_tasks(self):
        """
        Обрабатывает импорт задач из папки или ZIP-архива.
        Позволяет пользователю выбрать папку или ZIP-файл.
        """
        filters = "ZIP Archives (*.zip);;All Files (*)"
        selected_path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт задач: Выберите папку или ZIP-архив",
            "",
            filters
        )

        if selected_path_str:
            selected_path = Path(selected_path_str)
            if selected_path.exists() and (selected_path.is_dir() or selected_path.suffix.lower() == '.zip'):
                success = self.task_manager.import_tasks(selected_path)
                if success and hasattr(self, 'update_task_lists'):
                    self.update_task_lists()
            else:
                QMessageBox.warning(self, "Неверный выбор", f"Выбранный путь не является папкой или .zip архивом:\n{selected_path}")
        self._hide_settings_panel()

    def _hide_settings_panel(self):
        """Скрывает панель настроек, если она открыта."""
        if hasattr(self, 'settings_ui') and self.settings_ui.settings_panel.isVisible():
            self.settings_ui.toggle_settings_panel()