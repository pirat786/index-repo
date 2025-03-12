#dialogs.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QDialogButtonBox

class SortDialog(QDialog):
    def __init__(self, sort_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите сортировку")
        self.setMinimumSize(300, 200)
        self.sort_callback = sort_callback
        layout = QVBoxLayout(self)
        for sort_type, label in [('name', "По имени"), ('created_time', "По времени создания"), ('priority', "По приоритету")]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, s=sort_type: self.sort_and_close(s))
            layout.addWidget(btn)
        button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def sort_and_close(self, sort_type):
        self.sort_callback(sort_type)
        self.accept()