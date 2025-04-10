# zadachi/UI/utils.py
from PySide6.QtWidgets import QMenu, QListWidgetItem, QMessageBox, QStyle
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtCore import Qt
from pathlib import Path
import logging

# --- ДОБАВИТЬ ИМПОРТ КОНСТАНТ ---
# Используем относительный импорт, предполагая, что папки 'cods' и 'UI'
# находятся внутри 'zadachi' и 'zadachi' доступна в PYTHONPATH
try:
    # Если запускается как часть пакета 'zadachi'
    from ..cods import constants as tm_constants
except ImportError:
    # Запасной вариант, если структура другая или запускается не как пакет
    # Это может потребовать настройки PYTHONPATH или быть менее надежным
    try:
        from cods import constants as tm_constants
    except ImportError as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: Не удалось импортировать константы из cods.constants: {e}")
        # Задаем пустые значения, чтобы избежать падения, но цвета не будут работать
        class MockConstants:
            STATUS_COLORS_DARK = {}
            STATUS_COLORS_LIGHT = {}
        tm_constants = MockConstants()
# --- КОНЕЦ ДОБАВЛЕНИЯ ИМПОРТА ---


# Вспомогательные функции для ошибок из миксинов
def _show_warning_mixin(widget, title, message):
    logging.warning(message)
    if widget and QMessageBox:  # Проверяем наличие widget
        QMessageBox.warning(widget, title, message)


def _show_critical_mixin(widget, title, message):
    logging.critical(message, exc_info=True)
    if widget and QMessageBox:
        QMessageBox.critical(widget, title, message)


class ListUpdateMixin:
    """Миксин для обновления списков и контекстного меню задач."""

    def show_context_menu(self, pos):
        """Показывает контекстное меню для задач (pending/completed)."""
        widget = self.sender()
        item = widget.itemAt(pos)
        if not item: return

        is_completed = (widget == self.completed_task_list_widget)
        task_manager_idx = item.data(Qt.UserRole)

        if task_manager_idx is None:
            # logging.warning(...) # Убрано
            return

        menu = QMenu(self)
        task_list = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks

        # Прямой доступ к элементу списка без доп. проверок
        task_data = task_list[task_manager_idx] # Может вызвать IndexError

        # --- Статус ---
        status_menu = menu.addMenu("Изменить статус")
        current_status = task_data.get('status', '?')
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Используем импортированную константу tm_constants
        for status in tm_constants.STATUS_OPTIONS:
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            action = status_menu.addAction(status)
            action.setEnabled(status != current_status)
            # Используем lambda для передачи аргументов
            action.triggered.connect(
                (lambda checked=False, s=status, i=task_manager_idx, c=is_completed:
                 self.change_status_action(i, s, c))
            )

        # --- Приоритет ---
        priority_menu = menu.addMenu("Изменить приоритет")
        current_priority = task_data.get('priority', '?')
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Используем импортированную константу tm_constants
        for priority in tm_constants.PRIORITY_LEVELS:
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---
            action = priority_menu.addAction(priority)
            action.setEnabled(priority != current_priority)
            # Используем lambda для передачи аргументов
            action.triggered.connect(
                (lambda checked=False, p=priority, i=task_manager_idx, c=is_completed:
                 self.change_priority_action(i, p, c))
            )

        # Показываем меню, если есть какие-либо действия
        if menu.actions():
             menu.exec(widget.mapToGlobal(pos))

    def change_status_action(self, task_manager_idx, status, is_completed):
        """Обработчик смены статуса из меню."""
        try:
            self.task_manager.change_status(task_manager_idx, status, is_completed)
            self.update_task_lists()
        except IndexError as e:
            _show_warning_mixin(self, "Ошибка", f"Задача не найдена ({e}).")
        except Exception as e:
            _show_critical_mixin(self, "Ошибка", f"Ошибка смены статуса: {e}")

    def change_priority_action(self, task_manager_idx, priority, is_completed):
        """Обработчик смены приоритета из меню."""
        success = self.task_manager.change_priority(task_manager_idx, priority, is_completed)
        if success:
             self._update_single_list(is_completed)

    def _save_item_changes(self, dialog, item_data, name_edit, desc_edit, item_manager_idx, is_task, is_completed):
        """Сохраняет изменения имени и описания."""
        try:
            old_name = item_data.get('name', '')
            new_name = name_edit.text().strip()
            new_description = desc_edit.toPlainText()
            if not new_name: _show_warning_mixin(dialog, "Ошибка", "Имя не может быть пустым."); return

            logging.debug(f"Сохранение {'задачи' if is_task else 'команды'} idx={item_manager_idx}, имя='{new_name}'")
            item_data['name'] = new_name
            item_data['description'] = new_description

            # Обновляем описание и сохраняем все через TaskManager
            self.task_manager.update_description(item_manager_idx, new_description, is_task, is_completed,
                                                 folder_key=self.current_folder if not is_task else None)

            # Если имя команды изменилось, переименовываем папку
            if not is_task and old_name != new_name:
                logging.debug(f"Переименование команды/папки: '{old_name}' -> '{new_name}'")
                try:
                    self.task_manager.rename_command_subfolder(self.current_folder, item_manager_idx, new_name)
                    # rename_command_subfolder уже вызвал save_tasks
                except (OSError, ValueError, IndexError) as rename_e:
                    item_data['name'] = old_name;
                    name_edit.setText(old_name)  # Откат
                    # Сообщение об ошибке уже показано
                    return
                except Exception as e:
                    item_data['name'] = old_name;
                    name_edit.setText(old_name)  # Откат
                    _show_critical_mixin(self, "Критическая ошибка", f"Ошибка переименования: {e}")
                    return

            # Если имя задачи изменилось - save_tasks уже был в update_description

            self._update_single_list(is_completed if is_task else None)  # Обновляем UI
            dialog.accept()

        except IndexError as e:
            _show_warning_mixin(self, "Ошибка", f"Не удалось сохранить: элемент не найден ({e}).")
        except Exception as e:
            _show_critical_mixin(self, "Критическая ошибка", f"Не удалось сохранить: {e}")

    # --- Конец _save_item_changes ---

    def _update_command_list(self):
        """Обновляет UI список команд/папок для текущей папки."""
        try:
            widget = self.command_list_widget
            widget.clear()
            current_key = self.current_folder
            logging.debug(f"Обновление UI команд для: '{current_key}'")

            # 1. Папки
            subfolders_data = []  # (display_name, full_key)
            for key in self.task_manager.useful_commands.keys():
                if key == 'root': continue
                is_direct_child = (current_key == 'root' and '/' not in key) or \
                                  (key.startswith(current_key + '/') and '/' not in key[len(current_key) + 1:])
                if is_direct_child: subfolders_data.append((Path(key).name, key))

            subfolders_data.sort(key=lambda x: x[0].lower())
            for display_name, full_key in subfolders_data:
                item = QListWidgetItem(f"[Папка] {display_name}")
                item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
                item.setData(Qt.UserRole, full_key)  # Сохраняем ключ папки
                widget.addItem(item)

            # 2. Команды
            commands = self.task_manager.useful_commands.get(current_key, [])
            self._populate_list(widget, commands, append=True)  # Добавляем команды

            logging.debug(f"UI команд обновлен. Элементов: {widget.count()}")
        except Exception as e:
            _show_critical_mixin(self, "Ошибка UI", f"Не удалось обновить список команд: {e}")

    # --- Конец _update_command_list ---

    def update_task_lists(self):
        """Обновляет все списки UI."""
        logging.debug("Полное обновление UI...")
        try:
            limit = 100
            self._populate_list(self.task_list_widget, self.task_manager.pending_tasks[:limit])
            self._populate_list(self.completed_task_list_widget, self.task_manager.completed_tasks[:limit])
            self._update_command_list()
            logging.debug("Полное обновление UI завершено.")
        except Exception as e:
            _show_critical_mixin(self, "Ошибка обновления UI", f"{e}")

    def _update_single_list(self, is_completed):
        """Обновляет один список UI."""
        try:
            limit = 100
            if is_completed is None:
                self._update_command_list()
            elif is_completed:
                self._populate_list(self.completed_task_list_widget, self.task_manager.completed_tasks[:limit])
            else:
                self._populate_list(self.task_list_widget, self.task_manager.pending_tasks[:limit])
        except Exception as e:
            _show_critical_mixin(self, "Ошибка обновления UI", f"{e}")

    def _populate_list(self, widget, items, append=False):
        """Заполняет QListWidget, используя импортированные константы."""
        if not append: widget.clear()

        # --- ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Получаем цвета из импортированного модуля констант
        status_colors = tm_constants.STATUS_COLORS_DARK if self.current_theme == "Dark" else tm_constants.STATUS_COLORS_LIGHT
        # --- КОНЕЦ ИЗМЕНЕНИЯ ---

        # Цвет для команд можно тоже вынести в константы
        cmd_color = QColor("#D9E0EE" if self.current_theme == "Dark" else "#1F2A44")

        # Получаем полные списки один раз для поиска индекса
        full_pending = self.task_manager.pending_tasks
        full_completed = self.task_manager.completed_tasks
        cmds_in_folder = self.task_manager.useful_commands.get(self.current_folder, [])
        current_row = widget.count() if append else 0

        for item_data in items:
            # Пропускаем не-словари
            if not isinstance(item_data, dict): continue

            list_item = QListWidgetItem()
            is_task = 'status' in item_data  # Определяем, задача это или команда
            manager_idx = None

            if is_task:
                # Формируем текст задачи
                text = f"{item_data.get('name', '?')} (Приоритет: {item_data.get('priority', '?')})"
                list_item.setText(text)
                # Устанавливаем цвет текста в зависимости от статуса
                status = item_data.get('status', '?')
                # Используем status_colors, полученные из констант
                list_item.setForeground(QBrush(
                    QColor(status_colors.get(status, "#FF0000"))))  # Красный по умолчанию, если статус неизвестен
                # Выделяем жирным высокий приоритет
                if item_data.get('priority') == "Высокий":
                    font = list_item.font();
                    font.setBold(True);
                    list_item.setFont(font)
                # Находим оригинальный индекс задачи в полном списке
                # (это может быть неэффективно для больших списков)
                full_list = full_completed if status == 'Выполнено' else full_pending
                # Прямой поиск индекса без try-except ValueError
                if item_data in full_list:  # Проверка на всякий случай
                    manager_idx = full_list.index(item_data)
                list_item.setData(Qt.UserRole, manager_idx)  # Индекс задачи

            else:  # Это команда
                text = item_data.get('name', '?')
                # Формируем строку с информацией о вложениях
                atts = []
                for k, pfx in [('ino_paths', 'INO'), ('py_paths', 'PY'), ('pdf_paths', 'PDF'), ('img_paths', 'IMG')]:
                    if item_data.get(k): atts.append(f"{pfx}({len(item_data[k])})")
                if atts: text += f" [{', '.join(atts)}]"
                list_item.setText(text)
                # Устанавливаем цвет для команд
                list_item.setForeground(QBrush(cmd_color))
                # Находим оригинальный индекс команды в списке для текущей папки
                # Прямой поиск индекса без try-except ValueError
                if item_data in cmds_in_folder:  # Проверка на всякий случай
                    manager_idx = cmds_in_folder.index(item_data)
                list_item.setData(Qt.UserRole + 1, manager_idx)  # Индекс команды (используем другой флаг UserRole+1)

            # Добавляем элемент в виджет
            if append:
                widget.insertItem(current_row, list_item);
                current_row += 1
            else:
                widget.addItem(list_item)

    # --- Конец _populate_list ---

    def filter_commands(self, text):
        """Фильтрует команды И папки в ТЕКУЩЕЙ папке UI по тексту."""
        widget = self.command_list_widget
        text = text.lower().strip()
        logging.debug(f"Фильтр UI команд '{self.current_folder}': '{text}'")

        try:
            # 1. Получаем данные для текущей папки
            subfolders_data = []  # Список кортежей (display_name, full_key)
            for key in self.task_manager.useful_commands.keys():
                if key == 'root': continue
                # Проверяем, является ли key прямым потомком current_folder
                is_direct_child = False
                if self.current_folder == 'root':
                    if '/' not in key:
                        is_direct_child = True
                elif key.startswith(self.current_folder + '/') and '/' not in key[len(self.current_folder) + 1:]:
                    is_direct_child = True

                if is_direct_child:
                    display_name = Path(key).name
                    subfolders_data.append((display_name, key))

            commands = self.task_manager.useful_commands.get(self.current_folder, [])

            # 2. Фильтруем папки И команды
            filtered_folders = []
            if text: # Фильтруем папки только если есть текст для поиска
                for name, key in subfolders_data:
                    if text in name.lower():
                        filtered_folders.append((name, key))
            else: # Если текста нет, показываем все папки
                filtered_folders = subfolders_data

            filtered_cmds = [c for c in commands if text in c.get('name', '').lower()]

            # 3. Обновляем виджет
            widget.clear()

            # Добавляем отфильтрованные папки
            filtered_folders.sort(key=lambda x: x[0].lower()) # Сортируем отфильтрованные папки
            for name, key in filtered_folders:
                item = QListWidgetItem(f"[Папка] {name}")
                item.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
                item.setData(Qt.UserRole, key) # Сохраняем ключ папки
                widget.addItem(item)
            filtered_cmds.sort(key=lambda x: x.get('name', '').lower()) # Сортируем отфильтрованные команды
            self._populate_list(widget, filtered_cmds, append=True) # append=True добавляет после папок

        except Exception as e:
            _show_critical_mixin(self, "Ошибка UI", f"Ошибка фильтрации команд: {e}")
            self._update_command_list() # В случае ошибки, показываем все снова

