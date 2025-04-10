
# UI/dialogs.py
from . import QDialog, QVBoxLayout, QLabel, QCheckBox, QDialogButtonBox, os

class FolderSelectionDialog(QDialog):
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор дополнительных папок")
        self.folder_path = folder_path
        self.selected_folders = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите дополнительные папки с файлами для включения:"))

        subfolders = [f for f in os.listdir(self.folder_path) if os.path.isdir(os.path.join(self.folder_path, f))]
        self.checkboxes = {}
        for folder in subfolders:
            checkbox = QCheckBox(folder)
            layout.addWidget(checkbox)
            self.checkboxes[folder] = checkbox

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_selected_folders(self):
        return [folder for folder, checkbox in self.checkboxes.items() if checkbox.isChecked()]