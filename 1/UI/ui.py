# START OF FILE ui.py

from PySide6.QtWidgets import (
    QWidget, QTabWidget, QListWidget, QLineEdit, QVBoxLayout, QHBoxLayout,
    QPushButton, QMenu, QListWidgetItem, QMessageBox, QStyle, QFrame, QApplication, QLayout,
    QDialog, QTextEdit, QLabel, QFileDialog, QDialogButtonBox, QCheckBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QUrl, QTimer, QRect, QPropertyAnimation, QEvent, QObject, QMimeData
from PySide6.QtGui import QBrush, QColor, QFont, QDesktopServices, QIcon, QDrag

from pathlib import Path
import os

from .dialogs import FolderSelectionDialog
from .utils import ListUpdateMixin, _show_warning_mixin, _show_critical_mixin
from .task_management import TaskManagementMixin
from .command_management import CommandManagementMixin
from .google_drive import GoogleDriveMixin
from .settings_and_themes import SettingsAndThemesMixin
from .export_import import ExportImportMixin
from cods.task_manager import TaskManager
from styles.styles import THEMES


class DraggableListWidget(QListWidget):
    def __init__(self, parent=None, app=None):
        super().__init__(parent)
        self.app = app
        if not app: pass

        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setDragDropOverwriteMode(False)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not self.app: return
        if not item or item.text().startswith("[Папка]"):
            super().startDrag(Qt.IgnoreAction);
            return

        command_manager_idx = item.data(Qt.UserRole + 1)
        if command_manager_idx is None:
            super().startDrag(Qt.IgnoreAction);
            return

        commands = self.app.task_manager.useful_commands.get(self.app.current_folder, [])
        if not (0 <= command_manager_idx < len(commands)):
            super().startDrag(Qt.IgnoreAction);
            return

        mime_data = QMimeData()
        mime_data.setText(item.text())
        mime_data.setData("application/x-taskmanager-command-index", str(command_manager_idx).encode('utf-8'))
        mime_data.setData("application/x-taskmanager-source-folder", self.app.current_folder.encode('utf-8'))

        drag = QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec_(Qt.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-taskmanager-command-index") and \
                event.source() == self:
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-taskmanager-command-index") and \
                event.source() == self:
            target_item = self.itemAt(event.pos())
            if target_item and target_item.text().startswith("[Папка]"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        target_item = self.itemAt(event.pos())
        if not target_item or not target_item.text().startswith("[Папка]"):
            event.ignore()
            return

        if not self.app: event.ignore(); return
        mime_data = event.mimeData()
        if not mime_data.hasFormat("application/x-taskmanager-command-index") or \
                not mime_data.hasFormat("application/x-taskmanager-source-folder"):
            event.ignore();
            return

        # Direct extraction without try-except
        source_command_idx = int(mime_data.data("application/x-taskmanager-command-index").data().decode('utf-8'))
        source_folder_key = mime_data.data("application/x-taskmanager-source-folder").data().decode('utf-8')

        target_folder_key = target_item.data(Qt.UserRole)
        if not target_folder_key:
            target_folder_name = target_item.text()[7:].strip()
            target_folder_key = target_folder_name if self.app.current_folder == 'root' else f"{self.app.current_folder}/{target_folder_name}"

        if source_folder_key != self.app.current_folder:
            event.ignore();
            return

        # Direct call without try-except
        success = self.app.task_manager.move_command(source_folder_key, source_command_idx, target_folder_key)
        if success:
            event.setDropAction(Qt.MoveAction)
            event.accept()
            self.app._update_command_list()
        else:
            event.ignore()


class TaskApp(QWidget, TaskManagementMixin, CommandManagementMixin, GoogleDriveMixin,
              SettingsAndThemesMixin, ExportImportMixin, ListUpdateMixin):
    def __init__(self, tasks_file):
        super().__init__()
        self.tasks_file = Path(tasks_file)
        self.current_folder = 'root'

        # Direct initialization without try-except
        self.task_manager = TaskManager(self.tasks_file)
        # If TaskManager init fails, the app will likely crash here or soon after.

        self.google_creds = None

        self.setWindowTitle("Задачник")
        self.setGeometry(100, 100, 900, 700)

        main_layout = QVBoxLayout(self)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        main_layout.addWidget(self.content_widget)

        # Direct initialization without try-except
        SettingsAndThemesMixin.__init__(self)
        self.current_theme = self.load_theme()
        self.init_ui()
        self.apply_theme()
        self.update_task_lists()
        self.check_google_auth_status()


    def init_ui(self):
        self.tabs = QTabWidget()
        self.content_layout.addWidget(self.tabs)

        self.pending_tab, self.task_list_widget = self._create_tab("Задачи")
        self.completed_tab, self.completed_task_list_widget = self._create_tab("Выполненные задачи")
        self.commands_tab, self.command_list_widget = self._create_tab("Команды", use_draggable=True)

        self._add_search_bar(self.pending_tab, self.task_list_widget, "Поиск задач...", "Фильтр задач",
                             self.filter_tasks)
        self._add_search_bar(self.completed_tab, self.completed_task_list_widget, "Поиск выполненных...",
                             "Фильтр выполненных", self.filter_completed_tasks)
        self._add_search_bar(self.commands_tab, self.command_list_widget, "Поиск команд...", "Фильтр команд",
                             self.filter_commands)

        self.command_nav_bar = self._create_command_nav_bar()
        self.commands_tab.layout().insertWidget(1, self.command_nav_bar)

        task_buttons = [
            {"text": "Добавить", "callback": self.add_task, "tooltip": "Создать новую задачу"},
            {"text": "Удалить", "callback": self.delete_task, "tooltip": "Удалить выбранную(ые) задачу(и)"},
            {"text": "Сортировать", "callback": self.open_sort_dialog, "tooltip": "Сортировать задачи"},
        ]
        completed_buttons = [
            {"text": "Удалить", "callback": self.delete_task, "tooltip": "Удалить выбранную(ые) задачу(и)"},
            {"text": "Сортировать", "callback": self.open_sort_dialog, "tooltip": "Сортировать задачи"},
        ]
        command_buttons = [
            {"text": "Добавить команду", "callback": self.add_command, "tooltip": "Создать новую команду в текущей "
                                                                                  "папке"},
            {"text": "Создать папку", "callback": self.add_command_folder, "tooltip": "Создать новую папку здесь"},
            {"text": "Прикрепить", "callback": self.attach_folders, "tooltip": "Прикрепить файлы/папки к выбранной "
                                                                               "команде"},
            {"text": "Удалить", "callback": self.delete_command_or_folder, "tooltip": "Удалить выбранную команду или "
                                                                                      "папку"},
        ]

        self._add_buttons(self.pending_tab.layout(), task_buttons)
        self._add_buttons(self.completed_tab.layout(), completed_buttons)
        self._add_buttons(self.commands_tab.layout(), command_buttons)

        self.command_list_widget.itemDoubleClicked.connect(self.open_folder_or_edit_command)
        self.command_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.command_list_widget.customContextMenuRequested.connect(self.show_command_context_menu)


    def _create_tab(self, title, use_draggable=False):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(5, 5, 5, 5)
        list_widget = DraggableListWidget(parent=tab, app=self) if use_draggable else QListWidget(parent=tab)
        list_widget.setObjectName(f"{title.replace(' ', '')}ListWidget")
        list_widget.setAlternatingRowColors(True)
        list_widget.setFont(QFont("Arial", 12))
        list_widget.itemClicked.connect(self.highlight_task)

        if not use_draggable:
            list_widget.itemDoubleClicked.connect(self.edit_description)
            list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(self.show_context_menu)
            list_widget.setSelectionMode(QListWidget.ExtendedSelection)
            list_widget.setToolTip("Двойной клик - редактировать. Правый клик - опции.")
        else:
            list_widget.setSelectionMode(QListWidget.SingleSelection)
            list_widget.setToolTip("DND команды на папку. DblClick: папка - вход, команда - ред.")

        layout.addWidget(list_widget)
        self.tabs.addTab(tab, title)
        return tab, list_widget

    def _add_search_bar(self, tab, list_widget, placeholder, tooltip, callback):
        search_bar = QLineEdit(placeholderText=placeholder)
        search_bar.setToolTip(tooltip)
        search_bar.textChanged.connect(callback)
        tab.layout().insertWidget(0, search_bar)
        return search_bar

    def _add_buttons(self, layout, buttons_info):
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        for btn_info in buttons_info:
            btn = QPushButton(btn_info["text"])
            btn.setToolTip(btn_info.get("tooltip", ""))
            btn.clicked.connect(btn_info["callback"])
            button_layout.addWidget(btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _create_command_nav_bar(self):
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 2, 0, 2)
        self.back_button = QPushButton()
        self.back_button.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.back_button.setToolTip("Назад")
        self.back_button.setFixedSize(30, 30)
        self.back_button.clicked.connect(self.go_back)
        self.back_button.setEnabled(False)
        self.current_path_label = QLabel("Папка: root")
        self.current_path_label.setStyleSheet("font-style: italic; color: grey;")
        nav_layout.addWidget(self.back_button)
        nav_layout.addWidget(self.current_path_label)
        nav_layout.addStretch()
        return nav_widget

    def update_command_nav_bar(self):
        is_root = (self.current_folder == 'root')
        self.back_button.setEnabled(not is_root)
        display_path = self.current_folder.replace('/', ' / ')
        self.current_path_label.setText(f"Папка: {display_path}")

    def _update_command_list(self):
        super()._update_command_list()
        self.update_command_nav_bar()

    def filter_completed_tasks(self, text):
        text = text.lower()
        # Direct filtering without try-except
        filtered = [t for t in self.task_manager.completed_tasks if text in t.get('name', '').lower()][:100]
        self._populate_list(self.completed_task_list_widget, filtered)
        # No error handling or fallback population without try-except

    def highlight_task(self, item):
        pass

    def move_command_back(self, item):
        if not item or self.current_folder == 'root': return
        command_idx = item.data(Qt.UserRole + 1)
        if command_idx is None:
             _show_warning_mixin(self, "Ошибка", "Не удалось определить команду."); # This would normally be removed too
             return
        parent_folder_key = '/'.join(self.current_folder.split('/')[:-1]) or 'root'
        # Direct call without try-except
        if self.task_manager.move_command(self.current_folder, command_idx, parent_folder_key):
            self._update_command_list()
        # No error handling without try-except

    def show_command_context_menu(self, pos):
        item = self.command_list_widget.itemAt(pos)
        if not item or item.text().startswith("[Папка]"): return
        menu = QMenu(self)
        if self.current_folder != 'root':
            back_action = menu.addAction("Вернуть назад")
            back_action.triggered.connect(lambda: self.move_command_back(item))
        if menu.actions(): menu.exec(self.command_list_widget.mapToGlobal(pos))

    def delete_command_or_folder(self):
        selected = self.command_list_widget.selectedItems()
        if not selected: _show_warning_mixin(self, "Ничего не выбрано", "Выберите элемент."); return # This would normally be removed too
        item = selected[0]
        item_text = item.text()
        is_folder = item_text.startswith("[Папка]")
        name_to_delete = item_text[7:].strip() if is_folder else item_text.split(' [')[0]
        confirm_msg = f"Удалить папку '{name_to_delete}' и всё её содержимое?" if is_folder else f"Удалить команду '{name_to_delete}'?"
        if QMessageBox.question(self, "Подтверждение", confirm_msg, QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes:
            # Direct deletion without try-except
            if is_folder:
                folder_key = item.data(Qt.UserRole)
                if not folder_key: folder_key = name_to_delete if self.current_folder == 'root' else f"{self.current_folder}/{name_to_delete}"
                if self.task_manager.delete_folder(folder_key): self._update_command_list()
            else:
                command_idx = item.data(Qt.UserRole + 1)
                if command_idx is None:
                     pass
                else:
                    self.task_manager.delete_command(self.current_folder, command_idx)
                    self._update_command_list()