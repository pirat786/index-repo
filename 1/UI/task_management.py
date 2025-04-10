# START OF FILE task_management.py

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QInputDialog, QMessageBox, QDialog, QVBoxLayout, QLineEdit, QTextEdit, QLabel,
    QListWidget, QListWidgetItem, QCheckBox, QPushButton, QMenu
)
from PySide6.QtGui import QFont, QBrush, QColor

from cods.dialogs import SortDialog
# Убираем импорт SortDialog, если он не используется напрямую здесь
# from cods.dialogs import SortDialog
from .utils import _show_warning_mixin, _show_critical_mixin
import logging # Уберем позже, если logging не нужен

# --- ДОБАВИТЬ ИМПОРТ КОНСТАНТ ---
try:
    # Относительный импорт
    from ..cods import constants as tm_constants
except ImportError:
    # Запасной вариант
    try:
        from cods import constants as tm_constants
    except ImportError as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось импортировать константы из cods.constants: {e}")
        # Заглушка, чтобы избежать падения, но функционал будет сломан
        class MockConstants:
            PRIORITY_LEVELS = ["Средний"] # Минимум для работы QInputDialog
            STATUS_OPTIONS = ["Не выполнено"]
        tm_constants = MockConstants()
# --- КОНЕЦ ДОБАВЛЕНИЯ ИМПОРТА ---

class TaskManagementMixin:
    def add_task(self):
        name, ok = QInputDialog.getText(self, "Новая задача", "Введите название задачи:")
        if ok and name:
            # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
            # Используем импортированную константу PRIORITY_LEVELS
            priority, ok = QInputDialog.getItem(self, "Приоритет", "Выберите приоритет:",
                                                tm_constants.PRIORITY_LEVELS, 1, False)
            # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            if ok:
                # Вызов метода из TaskManager (теперь в task_mixin)
                self.task_manager.add_task(name, priority)
                # Обновление UI списка
                # _update_single_list использует _populate_list, который мы уже исправили
                self._update_single_list(False)

    def delete_task(self):
        selected_pending = self.task_list_widget.selectedItems()
        selected_completed = self.completed_task_list_widget.selectedItems()

        tasks_to_delete_pending_indices = [item.data(Qt.UserRole) for item in selected_pending]
        tasks_to_delete_completed_indices = [item.data(Qt.UserRole) for item in selected_completed]

        # Фильтруем None значения на случай, если data не была установлена
        tasks_to_delete_pending = [(idx, False) for idx in tasks_to_delete_pending_indices if idx is not None]
        tasks_to_delete_completed = [(idx, True) for idx in tasks_to_delete_completed_indices if idx is not None]

        if tasks_to_delete_pending or tasks_to_delete_completed:
            if QMessageBox.question(self, "Удаление", "Удалить выбранные задачи?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                error_occurred = False
                all_tasks_to_delete = sorted(tasks_to_delete_completed + tasks_to_delete_pending, key=lambda x: x[0],
                                             reverse=True)

                for idx, is_completed in all_tasks_to_delete:
                    success = self.task_manager.delete_task(idx, is_completed)
                    if not success:
                         error_occurred = True # Менеджер должен был показать ошибку, если она была

                if error_occurred:
                    # Сообщение об ошибке уже должно было быть показано менеджером
                    pass

                self.update_task_lists()


    def edit_description(self, item):
        list_widget = item.listWidget()
        is_completed = list_widget == self.completed_task_list_widget
        original_task_index = item.data(Qt.UserRole)

        # Проверка индекса (оставлена минимальная)
        if original_task_index is None:
            # _show_warning_mixin(self, "Ошибка", "Не удалось найти задачу для редактирования (нет индекса).")
            # Вместо вывода ошибки просто выходим
            return

        task_list = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
        # Проверка индекса (оставлена минимальная)
        if not (0 <= original_task_index < len(task_list)):
            # _show_warning_mixin(self, "Ошибка", "Не удалось найти задачу для редактирования (неверный индекс).")
            # Вместо вывода ошибки просто выходим
            return
        task = task_list[original_task_index]

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование: {task['name']}")
        layout = QVBoxLayout(dialog)

        name_edit = QLineEdit(task['name'])
        layout.addWidget(name_edit)

        time_info = f"Создано: {task.get('created_time', 'N/A')}\nНачало: {task.get('started_time', 'N/A')}\nВыполнено: {task.get('completed_time', 'N/A')}"
        time_label = QLabel(time_info)
        time_label.setFont(QFont("Arial", 10))
        time_label.setMinimumHeight(60)
        layout.addWidget(time_label)

        desc_edit = QTextEdit()
        description = task.get('description', '') or ""
        desc_edit.setPlainText(str(description))
        layout.addWidget(desc_edit)

        # --- Секция Подзадач ---
        # Создаем виджеты
        subtasks_label = QLabel("Подзадачи:")
        subtasks_list = QListWidget()
        add_subtask_button = QPushButton("Добавить подзадачу")

        # Сохраняем ссылки на виджеты в диалоге для доступа из других методов
        dialog.subtasks_label = subtasks_label
        dialog.subtasks_list = subtasks_list
        dialog.add_subtask_button = add_subtask_button # Сохраняем кнопку

        # Добавляем виджеты в layout (порядок важен для скрытия/показа)
        layout.addWidget(subtasks_label)
        layout.addWidget(subtasks_list)
        layout.addWidget(add_subtask_button)

        # Сохраняем контекст задачи в диалоге
        dialog.task_idx = original_task_index
        dialog.is_completed = is_completed

        # Заполняем список и управляем видимостью секции
        self._populate_subtasks(dialog) # Передаем весь диалог

        # Подключаем сигнал кнопки добавления
        add_subtask_button.clicked.connect(lambda: self._add_subtask(dialog))
        # --- Конец Секции Подзадач ---


        save_button = QPushButton("Сохранить")
        # Передаем is_task=True, так как это точно задача
        save_button.clicked.connect(
            lambda: self._save_item_changes(dialog, task, name_edit, desc_edit, original_task_index, True, is_completed)
        )
        layout.addWidget(save_button)

        dialog.setMinimumSize(600, 400)
        dialog.exec()

    def _populate_subtasks(self, dialog): # Принимает диалог
        # Получаем виджеты и контекст из диалога
        subtasks_list = dialog.subtasks_list
        task_idx = dialog.task_idx
        is_completed = dialog.is_completed
        subtasks_label = dialog.subtasks_label
        add_subtask_button = dialog.add_subtask_button

        subtasks_list.clear()
        subtasks_list.setWordWrap(True)
        subtasks_list.setStyleSheet("QListWidget::item { height: 30px; }")
        subtasks_list.setContextMenuPolicy(Qt.CustomContextMenu)
        # Отключаем старый коннект перед подключением нового, чтобы избежать дублирования
        # (не используем try)
        try: subtasks_list.customContextMenuRequested.disconnect()
        except: pass
        subtasks_list.customContextMenuRequested.connect(
            lambda pos: self._show_subtask_context_menu(pos, dialog)) # Передаем диалог

        subtasks_list.setDragEnabled(True)
        subtasks_list.setAcceptDrops(True)
        subtasks_list.setDragDropMode(QListWidget.InternalMove)
        subtasks_list.setDefaultDropAction(Qt.MoveAction)
        subtasks_list.setSelectionMode(QListWidget.SingleSelection)
        subtasks_list.setDropIndicatorShown(True)
        subtasks_list.setDragDropOverwriteMode(False)
        subtasks_list.setMovement(QListWidget.Snap)

        subtasks_list.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        subtasks_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        subtasks_list.setAutoScroll(True)
        subtasks_list.setAutoScrollMargin(20)

        task_list_tm = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
        # Проверка индекса (минимальная)
        if not (0 <= task_idx < len(task_list_tm)):
             return
        subtasks = task_list_tm[task_idx].get('subtasks', [])

        for i, subtask in enumerate(subtasks):
            item = QListWidgetItem()
            checkbox = QCheckBox(f"{i + 1}) {subtask['name']}")
            checkbox.setChecked(subtask['completed'])
            checkbox.setFocusPolicy(Qt.NoFocus)
            item.setData(Qt.UserRole, i) # Сохраняем оригинальный индекс

            if not is_completed:
                # Используем lambda с захватом переменных для stateChanged
                # Убедимся, что коннект не дублируется (хотя для checkbox это менее критично)
                checkbox.stateChanged.connect(
                    (lambda captured_i=i, tidx=task_idx, comp=is_completed:
                     lambda state: self._toggle_subtask_ui(tidx, captured_i, comp, state))()
                )
            else:
                checkbox.setEnabled(False)

            subtasks_list.addItem(item)
            subtasks_list.setItemWidget(item, checkbox)

        # --- Управление видимостью секции подзадач ---
        has_subtasks = subtasks_list.count() > 0
        subtasks_label.setVisible(has_subtasks)
        subtasks_list.setVisible(has_subtasks)
        # Кнопка "Добавить" видна, если задача НЕ завершена
        add_subtask_button.setVisible(not is_completed)
        # --- Конец управления видимостью ---

        # Переподключаем сигнал rowsMoved
        model = subtasks_list.model()
        if model:
            # Отключаем все предыдущие подключения к этому сигналу
            try: model.rowsMoved.disconnect()
            except: pass
            # Подключаем заново, передавая диалог
            model.rowsMoved.connect(lambda p, s, e, d, r: self._on_subtasks_reordered(dialog))


    def _toggle_subtask_ui(self, task_idx, subtask_original_idx, is_completed, state):
        success = self.task_manager.toggle_subtask(task_idx, subtask_original_idx, is_completed)
        if not success:
            # Менеджер должен был показать ошибку
            # Можно попробовать откатить UI, но это сложнее
            pass

    def _on_subtasks_reordered(self, dialog): # Принимает диалог
        subtasks_list = dialog.subtasks_list
        task_idx = dialog.task_idx
        is_completed = dialog.is_completed

        task_list_tm = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
        if not (0 <= task_idx < len(task_list_tm)):
            return
        original_subtasks = task_list_tm[task_idx].get('subtasks', [])
        if not original_subtasks: return

        original_indices_new_order = []
        valid_indices = True
        for i in range(subtasks_list.count()):
            item = subtasks_list.item(i)
            if not item:
                valid_indices = False; break
            original_index = item.data(Qt.UserRole)
            # Проверка на None и диапазон (минимальная)
            if original_index is None or not (0 <= original_index < len(original_subtasks)):
                valid_indices = False; break
            original_indices_new_order.append(original_index)

        # Проверка количества
        if not valid_indices or len(original_indices_new_order) != len(original_subtasks):
            # _show_critical_mixin(self, "Ошибка", "Произошла ошибка при сохранении порядка подзадач. Порядок не изменен.")
            # QTimer.singleShot(0, lambda: self._populate_subtasks(dialog)) # Восстанавливаем UI
            return

        new_subtasks_order = [original_subtasks[i] for i in original_indices_new_order]

        task_list_tm[task_idx]['subtasks'] = new_subtasks_order
        # Сохраняем (без try)
        success = self.task_manager.save_tasks()
        if not success:
             # _show_critical_mixin(self, "Ошибка", "Не удалось сохранить новый порядок подзадач.")
             # self.task_manager.load_tasks() # Восстановление?
             # QTimer.singleShot(0, lambda: self._populate_subtasks(dialog))
             return

        # Обновляем нумерацию и данные в UI через QTimer
        QTimer.singleShot(0, lambda: self._populate_subtasks(dialog))

    def _show_subtask_context_menu(self, pos, dialog): # Принимает диалог
        subtasks_list = dialog.subtasks_list
        task_idx = dialog.task_idx
        is_completed = dialog.is_completed

        item = subtasks_list.itemAt(pos)
        if item:
            original_subtask_idx = item.data(Qt.UserRole)
            if original_subtask_idx is None: # Проверка на None
                return

            menu = QMenu(self)

            # Проверка, что контекст диалога совпадает (минимальная)
            if dialog.task_idx != task_idx or dialog.is_completed != is_completed:
                # logging.warning("Контекстное меню подзадачи: не найден корректный диалог.")
                return

            if not is_completed:
                edit_action = menu.addAction("Редактировать подзадачу")
                # Передаем диалог и индекс
                edit_action.triggered.connect(lambda checked=False, d=dialog, idx=original_subtask_idx: self._edit_subtask(d, idx))

                delete_action = menu.addAction("Удалить подзадачу")
                # Передаем диалог и индекс
                delete_action.triggered.connect(lambda checked=False, d=dialog, idx=original_subtask_idx: self._delete_subtask(d, idx))

            # Показываем меню, только если есть действия
            if menu.actions():
                menu.exec(subtasks_list.mapToGlobal(pos))

    def _delete_subtask(self, dialog, subtask_original_idx):
        task_idx = dialog.task_idx
        is_completed = dialog.is_completed
        # subtasks_list = dialog.subtasks_list # Не используется напрямую здесь

        task_list = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
        # Минимальная проверка индекса
        if not (0 <= task_idx < len(task_list) and 'subtasks' in task_list[
            task_idx] and 0 <= subtask_original_idx < len(task_list[task_idx]['subtasks'])):
            # _show_warning_mixin(self, "Ошибка", "Не удалось найти подзадачу для удаления.")
            return

        subtask_name = task_list[task_idx]['subtasks'][subtask_original_idx]['name']
        if QMessageBox.question(self, "Удаление", f"Удалить подзадачу '{subtask_name}'?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            task_list[task_idx]['subtasks'].pop(subtask_original_idx)
            # Сохраняем (без try)
            success = self.task_manager.save_tasks()
            if success:
                # Обновляем список и видимость секции
                self._populate_subtasks(dialog)
                # Если подзадач не осталось, populate скроет секцию
            else:
                # _show_critical_mixin(self, "Ошибка", "Не удалось сохранить изменения после удаления подзадачи.")
                # Можно добавить load_tasks для восстановления
                # self.task_manager.load_tasks()
                self._populate_subtasks(dialog)  # Обновляем UI в любом случае

    def _edit_subtask(self, dialog, subtask_original_idx): # Принимает диалог
        task_idx = dialog.task_idx
        is_completed = dialog.is_completed
        # subtasks_list = dialog.subtasks_list # Не используется напрямую здесь

        task_list = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
        # Минимальная проверка индекса
        if not (0 <= task_idx < len(task_list) and 'subtasks' in task_list[task_idx] and 0 <= subtask_original_idx < len(task_list[task_idx]['subtasks'])):
            # _show_warning_mixin(self, "Ошибка", "Не удалось найти подзадачу для редактирования.")
            return

        subtask = task_list[task_idx]['subtasks'][subtask_original_idx]
        new_name, ok = QInputDialog.getText(self, "Редактировать подзадачу", "Введите новое название подзадачи:",
                                            QLineEdit.Normal, subtask['name'])

        if ok and new_name:
            task_list[task_idx]['subtasks'][subtask_original_idx]['name'] = new_name
            # Сохраняем (без try)
            success = self.task_manager.save_tasks()
            if success:
                self._populate_subtasks(dialog) # Обновляем список
            else:
                # _show_critical_mixin(self, "Ошибка", "Не удалось сохранить изменения подзадачи.")
                # self.task_manager.load_tasks() # Восстановление?
                self._populate_subtasks(dialog) # Обновляем UI

    def _add_subtask(self, dialog):
        task_idx = dialog.task_idx
        is_completed = dialog.is_completed
        # subtasks_list = dialog.subtasks_list # Не используется напрямую здесь

        subtask_name, ok = QInputDialog.getText(self, "Новая подзадача", "Введите название подзадачи:")
        if ok and subtask_name:
            # Сохраняем через менеджер (без try)
            success = self.task_manager.add_subtask(task_idx, subtask_name, is_completed)
            if success:
                # --- Показываем секцию, если она была скрыта ---
                # Проверяем, была ли это первая подзадача
                task_list = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
                if 0 <= task_idx < len(task_list) and len(task_list[task_idx].get('subtasks', [])) == 1:
                     dialog.subtasks_label.setVisible(True)
                     dialog.subtasks_list.setVisible(True)
                     # Кнопка уже должна быть видима, если задача не завершена
                # --- Конец показа секции ---

                self._populate_subtasks(dialog) # Обновляем список (и видимость)
            else:
                 # Менеджер должен был показать ошибку сохранения
                 # Можно добавить load_tasks для восстановления, но это проверка
                 # self.task_manager.load_tasks() # Попробуем восстановить
                 self._populate_subtasks(dialog) # Обновляем UI в любом случае

    def change_priority(self, item, priority):
        # Получаем индекс из данных элемента
        original_task_index = item.data(Qt.UserRole)
        if original_task_index is None:
            _show_warning_mixin(self, "Ошибка", "Не удалось изменить приоритет: задача не найдена (нет индекса).")
            return

        list_widget = item.listWidget()
        is_completed = list_widget == self.completed_task_list_widget

        success = self.task_manager.change_priority(original_task_index, priority, is_completed)
        if success:
            self._update_single_list(is_completed)
        # else: Менеджер должен был показать ошибку

    def open_sort_dialog(self):

        SortDialog(self.sort_tasks, self).exec()

    def sort_tasks(self, by='name'):
        success = self.task_manager.sort_tasks(by)
        if success:
            self.update_task_lists()
        # else: Менеджер должен был показать ошибку

    def filter_tasks(self, text):
        text = text.lower()
        # Получаем полные списки из менеджера
        all_pending = self.task_manager.pending_tasks
        all_completed = self.task_manager.completed_tasks

        # Фильтруем и обрезаем до 100
        filtered_pending = [
            (idx, t) for idx, t in enumerate(all_pending)
            if text in t.get('name', '').lower() or text in t.get('description', '').lower()
        ]
        filtered_completed = [
            (idx, t) for idx, t in enumerate(all_completed)
            if text in t.get('name', '').lower() or text in t.get('description', '').lower()
        ]

        # Обновляем виджеты с отфильтрованными данными и их оригинальными индексами
        self._populate_list(self.task_list_widget, filtered_pending)
        self._populate_list(self.completed_task_list_widget, filtered_completed)
