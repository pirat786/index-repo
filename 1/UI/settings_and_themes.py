# START OF FILE settings_and_themes.py

from . import (
    QFileDialog, QMessageBox, THEMES, SETTINGS_FOLDER, SETTINGS_FILE,
    CURRENT_VERSION, _save_json, _load_json, json, pickle, Path, TaskManager
)

class SettingsAndThemesMixin:
    def __init__(self):
        from .ui_settings import SettingsUI
        self.settings_ui = SettingsUI(self)

    def _handle_settings(self, mode='load', theme=None):
        settings_path = SETTINGS_FILE
        SETTINGS_FOLDER.mkdir(exist_ok=True)
        if mode == 'load':
            if settings_path.exists():
                with settings_path.open('r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    return loaded_settings.get('theme', 'Dark')
            return 'Dark'
        elif mode == 'save' and theme:
            settings = {'theme': theme, 'tasks_folder': str(self.tasks_file.parent)}
            with settings_path.open('w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)

    def load_theme(self):
        return self._handle_settings(mode='load')

    def save_theme(self, theme):
        self._handle_settings(mode='save', theme=theme)

    def apply_theme(self):
        self.setStyleSheet(THEMES[self.current_theme])
        self.update_task_lists()
        self.task_list_widget.repaint()
        self.completed_task_list_widget.repaint()
        self.command_list_widget.repaint()

    def toggle_theme(self):
        themes = ["Dark", "Light"]
        current_index = themes.index(self.current_theme)
        next_index = (current_index + 1) % len(themes)
        self.current_theme = themes[next_index]
        self.save_theme(self.current_theme)
        self.apply_theme()
        if self.settings_ui.settings_panel.isVisible():
            self.settings_ui.toggle_settings_panel()

    def open_settings_dialog(self):
        if self.settings_ui.settings_panel.isVisible():
            self.settings_ui.toggle_settings_panel()
        from .ui_settings import SettingsDialog
        dialog = SettingsDialog(self)
        dialog.exec()

    def show_help(self):
        from .ui_settings import HelpDialog
        HelpDialog(self).exec()
        if self.settings_ui.settings_panel.isVisible():
            self.settings_ui.toggle_settings_panel()

    def change_tasks_folder(self):
        new_folder = QFileDialog.getExistingDirectory(self, "Выберите новую папку для хранения задач",
                                                      str(self.tasks_file.parent))
        if new_folder:
            new_folder_path = Path(new_folder)
            new_folder_path.mkdir(exist_ok=True)
            new_tasks_file = new_folder_path / "tasks.json"

            self.task_manager.save_tasks()
            self.tasks_file = new_tasks_file
            self.task_manager = TaskManager(self.tasks_file)

            if self.tasks_file.exists():
                self.task_manager.load_tasks()
            else:
                data = {
                    'version': CURRENT_VERSION,
                    'pending': self.task_manager.pending_tasks,
                    'completed': self.task_manager.completed_tasks,
                    'useful_commands': self.task_manager.useful_commands
                }
                _save_json(self.tasks_file, data)

            self.update_task_lists()
            self.save_theme(self.current_theme)
            if self.google_creds:
                token_file = SETTINGS_FILE.with_suffix('.pickle')
                token_file.parent.mkdir(exist_ok=True)
                with token_file.open("wb") as f:
                    pickle.dump(self.google_creds, f)
            QMessageBox.information(self, "Успех", f"Папка задач изменена на {new_folder}")
            if self.settings_ui.settings_panel.isVisible():
                self.settings_ui.toggle_settings_panel()