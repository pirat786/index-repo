from imports.imports import (
    sys,
    os,
    QApplication,
    QIcon,
)
from UI.ui import TaskApp
from cods.task_manager import load_or_set_tasks_folder

if __name__ == "__main__":
    app = QApplication(sys.argv)
    tasks_file = load_or_set_tasks_folder()  # Получаем TASKS_FILE
    window = TaskApp(tasks_file)  # Передаём TASKS_FILE в TaskApp

    # Устанавливаем иконку окна приложения
    icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "zadachi_icon.ico"))
    window.setWindowIcon(QIcon(icon_path))

    window.show()

    sys.exit(app.exec())