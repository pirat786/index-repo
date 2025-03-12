#main.py
import sys
from PySide6.QtWidgets import QApplication
from ui import TaskApp
from task_manager import load_or_set_tasks_folder

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tasks_file = load_or_set_tasks_folder()  # Получаем TASKS_FILE
    window = TaskApp(tasks_file)  # Передаём TASKS_FILE в TaskApp
    window.show()
    sys.exit(app.exec())