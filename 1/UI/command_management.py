# START OF FILE command_management.py

from mimetypes import types_map

from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import (
    QInputDialog, QMessageBox, QDialog, QVBoxLayout, QLineEdit, QTextEdit, QLabel,
    QListWidget, QPushButton, QMenu, QDialogButtonBox, QCheckBox, QFileDialog,
    QListWidgetItem, QHBoxLayout, QFrame
)
from PySide6.QtGui import QDesktopServices, QColor, QFont

from pathlib import Path
import os
import shutil

from .dialogs import FolderSelectionDialog
from .utils import _show_warning_mixin, _show_critical_mixin


class CommandManagementMixin:

    def add_command(self):
        name, ok = QInputDialog.getText(self, "Новая команда", "Введите название команды:")
        if not (ok and name): return

        success, _ = self.task_manager.add_command(name, folder_key=self.current_folder)
        if not success:
            return

        commands_in_folder = self.task_manager.useful_commands.get(self.current_folder, [])
        command_manager_idx = len(commands_in_folder) - 1
        if command_manager_idx < 0 or commands_in_folder[command_manager_idx]['name'] != name:
            self._update_command_list();
            return

        attach_type, ok2 = QInputDialog.getItem(self, "Прикрепить файлы/папку?", "Хотите прикрепить ресурсы?",
                                                self._get_attachment_options(), 0, False)
        if ok2 and attach_type != "Ничего":
            self._handle_attachment_selection(attach_type, command_manager_idx, self.current_folder, parent_dialog=None)

        self._update_command_list()

    def add_command_folder(self):
        folder_name, ok = QInputDialog.getText(self, "Новая папка", "Введите название папки:")
        if ok and folder_name:
            success = self.task_manager.add_command_folder(folder_name, base_folder_key=self.current_folder)
            if success:
                self._update_command_list()

    def edit_command_description(self, item):
        if not item or item.text().startswith("[Папка]"): return

        command_manager_idx = item.data(Qt.UserRole + 1)
        if command_manager_idx is None: _show_warning_mixin(self, "Ошибка", "Нет индекса команды."); return

        commands_in_folder = self.task_manager.useful_commands.get(self.current_folder, [])
        if not (0 <= command_manager_idx < len(commands_in_folder)):
            _show_warning_mixin(self, "Ошибка", "Неверный индекс команды.");
            return

        command_data = commands_in_folder[command_manager_idx]

        dialog = QDialog(self)
        dialog.setObjectName("EditCommandDialog")
        dialog.setWindowTitle(f"Редактирование: {command_data['name']}")
        dialog.setMinimumSize(600, 450)
        layout = QVBoxLayout(dialog)

        name_edit = QLineEdit(command_data['name'])
        name_edit.setObjectName("commandNameEdit")
        layout.addWidget(QLabel("Имя команды:"))
        layout.addWidget(name_edit)
        desc_edit = QTextEdit()
        desc_edit.setObjectName("commandDescEdit")
        desc_edit.setPlainText(command_data.get('description', '') or "")
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(desc_edit)

        self._add_attached_files_ui(layout, command_data, command_manager_idx, dialog)

        button_box = QDialogButtonBox()
        save_btn = button_box.addButton("Сохранить", QDialogButtonBox.AcceptRole)
        attach_btn = button_box.addButton("Прикрепить/Изменить", QDialogButtonBox.ActionRole)
        cancel_btn = button_box.addButton("Отмена", QDialogButtonBox.RejectRole)
        layout.addWidget(button_box)

        save_btn.clicked.connect(
            lambda chk=False, d=dialog, data=command_data, n=name_edit, desc=desc_edit, idx=command_manager_idx:
            self._save_item_changes(d, data, n, desc, idx, False, None)
        )
        attach_btn.clicked.connect(
            lambda chk=False, idx=command_manager_idx, fldr=self.current_folder, dlg=dialog:
            self._open_attach_dialog(idx, fldr, dlg)
        )
        cancel_btn.clicked.connect(dialog.reject)

        dialog.exec()

    def _add_attached_files_ui(self, parent_layout, command_data, command_manager_idx, parent_dialog):
        # Создаем QFrame как контейнер для секции
        files_frame = QFrame()
        files_frame.setObjectName("filesSectionFrame")  # Даем имя для поиска
        files_frame.setFrameShape(QFrame.NoFrame)  # Убираем рамку у фрейма

        # Layout для содержимого фрейма
        files_layout = QVBoxLayout(files_frame)  # Устанавливаем layout НА фрейм
        files_layout.setContentsMargins(0, 5, 0, 5)  # Небольшие отступы сверху/снизу

        files_layout.addWidget(QLabel("Прикрепленные ресурсы:"))
        files_list = QListWidget()
        files_list.setObjectName("attachedFilesList")
        files_list.setSelectionMode(QListWidget.ExtendedSelection)
        files_layout.addWidget(files_list)

        # Сохраняем виджет списка на диалоге для удобства доступа
        parent_dialog.attached_files_list_widget = files_list

        # Заполняем список и получаем карту путей
        parent_dialog.attached_files_paths_map = self._populate_attached_files(command_data, files_list)

        # Кнопки управления файлами
        files_btn_layout = QHBoxLayout()
        view_btn = QPushButton("Просмотреть")
        view_btn.setObjectName("viewAttachedButton")
        view_btn.clicked.connect(
            lambda: self._view_selected_attached_files(files_list, parent_dialog.attached_files_paths_map))
        remove_btn = QPushButton("Удалить выбранное")
        remove_btn.setObjectName("removeAttachedButton")
        remove_btn.clicked.connect(
            lambda chk=False, w=files_list, idx=command_manager_idx, fldr=self.current_folder, dlg=parent_dialog:
            self._remove_selected_attachments(w, idx, fldr, dlg)
        )
        files_btn_layout.addWidget(view_btn)
        files_btn_layout.addWidget(remove_btn)
        files_btn_layout.addStretch()
        files_layout.addLayout(files_btn_layout)  # Добавляем кнопки в layout фрейма

        # Добавляем сам фрейм в layout родительского диалога
        parent_layout.addWidget(files_frame)

        # --- Управление видимостью ---
        # Проверяем, есть ли реальные файлы (не считая заглушку "Нет прикрепленных...")
        has_items = files_list.count() > 0 and "Нет прикрепленных" not in files_list.item(0).text()
        files_frame.setVisible(has_items)  # Показываем/скрываем весь фрейм
        # --- Конец управления видимостью ---

        # Устанавливаем состояние кнопок просмотра/удаления
        view_btn.setEnabled(has_items)
        remove_btn.setEnabled(has_items)
        # Убедимся, что сам список доступен только если есть элементы
        files_list.setEnabled(has_items)

    def _populate_attached_files(self, command_data, files_list_widget):
        files_list_widget.clear()
        full_paths_map = {}
        subfolder_rel = command_data.get('subfolder')

        if not subfolder_rel:
            files_list_widget.addItem("Нет прикрепленных ресурсов (нет субфолдера).")
            files_list_widget.setEnabled(False)
            return full_paths_map

        subfolder_abs = self.tasks_file.parent / subfolder_rel
        types_map = {'ino_paths': '[INO]', 'py_paths': '[PY]', 'pdf_paths': '[PDF]', 'img_paths': '[IMG]'}
        has_attachments = False

        for key, prefix in types_map.items():
            relative_paths = command_data.get(key, [])
            for rel_path in relative_paths:
                display_text = f"{prefix} {rel_path}"
                full_abs_path = subfolder_abs / rel_path
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, str(full_abs_path))
                item.setData(Qt.UserRole + 1, key)
                full_paths_map[display_text] = str(full_abs_path)

                if not full_abs_path.exists():
                    item.setForeground(QColor("red"));
                    item.setToolTip(f"НЕ НАЙДЕНО:\n{full_abs_path}")
                else:
                    item.setToolTip(f"Путь:\n{full_abs_path}")

                files_list_widget.addItem(item)
                has_attachments = True

        if not has_attachments:
            files_list_widget.addItem("Нет прикрепленных ресурсов.")
            files_list_widget.setEnabled(False)
        else:
            files_list_widget.setEnabled(True)

        return full_paths_map

    def _view_selected_attached_files(self, files_list_widget, full_paths_map):
        selected_items = files_list_widget.selectedItems()
        if not selected_items: _show_warning_mixin(self, "Нет выбора", "..."); return

        for item in selected_items:
            full_path_str = item.data(Qt.UserRole)
            if full_path_str:
                full_path = Path(full_path_str)
                if full_path.exists():
                    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(full_path))):
                        _show_warning_mixin(self, "Ошибка", f"Не удалось открыть '{full_path.name}'.")
                else:
                    _show_warning_mixin(self, "Ошибка", f"Ресурс не найден:\n{full_path}")

    def attach_folders(self):
        selected = self.command_list_widget.selectedItems()
        if not selected: _show_warning_mixin(self, "Нет выбора", "..."); return
        item = selected[0]
        if item.text().startswith("[Папка]"): _show_warning_mixin(self, "Неверный выбор", "..."); return
        command_manager_idx = item.data(Qt.UserRole + 1)
        if command_manager_idx is None: _show_warning_mixin(self, "Ошибка", "..."); return
        self._open_attach_dialog(command_manager_idx, self.current_folder, parent_dialog=None)

    def _open_attach_dialog(self, command_manager_idx, folder_key, parent_dialog=None):
        attach_type, ok = QInputDialog.getItem(self, "Прикрепить/Изменить", "Выберите тип ресурса:",
                                               self._get_attachment_options()[1:], 0, False)
        if ok:
            self._handle_attachment_selection(attach_type, command_manager_idx, folder_key, parent_dialog)

    def _get_attachment_options(self):
        return ["Ничего", "Папку с .ino", "Папку с .py", "PDF файлы", "Изображения (PNG/JPG и др.)"]

    def _handle_file_selection(self, attach_type, parent=None):
        attachments = {'ino_folder': None, 'py_folder': None, 'additional_folders': None, 'pdf_files': None,
                       'img_files': None}
        if attach_type == "Папку с .ino":
            folder = QFileDialog.getExistingDirectory(parent, "Выберите папку INO", "")
            if folder: attachments['ino_folder'] = folder
        elif attach_type == "Папку с .py":
            folder = QFileDialog.getExistingDirectory(parent, "Выберите папку PY", "")
            if folder:
                attachments['py_folder'] = folder
                subfolders = [f for f in os.listdir(folder) if
                              os.path.isdir(os.path.join(folder, f)) and f not in ['.git', '.venv', 'venv',
                                                                                   '__pycache__']]
                if subfolders:
                    dialog = FolderSelectionDialog(folder, parent)
                    if dialog.exec(): attachments['additional_folders'] = dialog.get_selected_folders()
                else:
                    attachments['additional_folders'] = []
        elif attach_type == "PDF файлы":
            files, _ = QFileDialog.getOpenFileNames(parent, "Выберите PDF", "", "PDF (*.pdf)")
            if files: attachments['pdf_files'] = files
        elif attach_type == "Изображения (PNG/JPG и др.)":
            files, _ = QFileDialog.getOpenFileNames(parent, "Выберите изображения", "",
                                                    "Images (*.png *.jpg *.jpeg *.gif *.bmp)")
            if files: attachments['img_files'] = files
        return attachments

    def _handle_attachment_selection(self, attach_type, command_manager_idx, folder_key, parent_dialog=None):
        options = {'folder_key': folder_key}
        attachments = self._handle_file_selection(attach_type, self)
        options.update({k: v for k, v in attachments.items() if v})

        if not any(k in options for k in ['ino_folder', 'py_folder', 'pdf_files', 'img_files']):
            # Если ничего не выбрано для прикрепления, выходим
            return

        # Вызываем менеджер для копирования и обновления данных (без try)
        success, copied_files = self.task_manager.update_command_folders(command_manager_idx, **options)

        if success:
            # Обновляем главный список команд в основном окне
            self._update_command_list()

            # Если диалог редактирования открыт, обновляем его секцию файлов
            if parent_dialog and parent_dialog.isVisible():
                 # Находим фрейм и список внутри него
                 files_frame = parent_dialog.findChild(QFrame, "filesSectionFrame")
                 files_list = parent_dialog.attached_files_list_widget # Используем сохраненную ссылку

                 # Проверяем, что нашли нужные виджеты
                 if files_frame and files_list:
                    # Получаем обновленные данные команды
                    commands_list = self.task_manager.useful_commands.get(folder_key, [])
                    # Минимальная проверка индекса
                    if isinstance(commands_list, list) and 0 <= command_manager_idx < len(commands_list):
                        command_data = commands_list[command_manager_idx]
                        # Перезаполняем список файлов в диалоге
                        parent_dialog.attached_files_paths_map = self._populate_attached_files(command_data, files_list)

                        # --- Показываем фрейм и обновляем кнопки ---
                        has_items = files_list.count() > 0 and "Нет прикрепленных" not in files_list.item(0).text()
                        files_frame.setVisible(True) # Убедимся, что фрейм видим после добавления
                        files_list.setEnabled(has_items)

                        # Обновляем состояние кнопок внутри фрейма
                        view_btn = files_frame.findChild(QPushButton, "viewAttachedButton")
                        remove_btn = files_frame.findChild(QPushButton, "removeAttachedButton")
                        if view_btn: view_btn.setEnabled(has_items)
                        if remove_btn: remove_btn.setEnabled(has_items)
                        # --- Конец обновления UI в диалоге ---
                    else:
                         # logging.warning("Не удалось найти обновленные данные команды в _handle_attachment_selection.")
                         pass # Не удалось получить данные, ничего не делаем с UI диалога
                 else:
                     # logging.warning("Не удалось найти files_frame или files_list в диалоге.")
                     pass # Не нашли виджеты, ничего не делаем

            # Сообщаем об успехе пользователю
            if copied_files:
                QMessageBox.information(self, "Успех", f"Ресурсы прикреплены ({len(copied_files)} скопировано).")
            else:
                # Если файлы уже были, копирования могло не быть
                 QMessageBox.information(self, "Успех", "Ресурсы прикреплены.")
        # else: Менеджер должен был показать ошибку

    def _remove_selected_attachments(self, files_list_widget, command_manager_idx, folder_key, parent_dialog):
        selected_items = files_list_widget.selectedItems()
        if not selected_items: # _show_warning_mixin(self, "Нет выбора", "...");
             return

        items_to_remove = []
        for item in selected_items:
            display_text = item.text()
            if ' ' not in display_text: continue # Пропускаем заглушку "Нет прикрепленных"
            rel_path = display_text.split(' ', 1)[1]
            type_key = item.data(Qt.UserRole + 1) # Ключ типа ('ino_paths', 'pdf_paths'...)
            if rel_path and type_key: items_to_remove.append((rel_path, type_key))

        if not items_to_remove: # _show_warning_mixin(self, "Ошибка", "Не удалось определить ресурсы.");
            return

        confirm_msg = "Удалить выбранное?\n" + "\n".join([f"- {p} ({k.split('_')[0].upper()})" for p, k in items_to_remove]) + "\n\nФайлы/папки будут удалены с диска!"
        if QMessageBox.question(self, "Подтверждение", confirm_msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes:
            commands_list = self.task_manager.useful_commands.get(folder_key)
            # Минимальная проверка
            if not isinstance(commands_list, list) or not (0 <= command_manager_idx < len(commands_list)):
                # _show_warning_mixin(self, "Ошибка", "Команда не найдена.")
                return
            command_data = commands_list[command_manager_idx]
            subfolder_rel = command_data.get('subfolder')

            if not subfolder_rel:
                # _show_warning_mixin(self, "Ошибка", "Субфолдер команды не найден.")
                return

            subfolder_abs = self.tasks_file.parent / subfolder_rel
            something_removed = False
            error_occurred = False # Флаг для ошибок удаления файлов

            types_map_keys = ['ino_paths', 'py_paths', 'pdf_paths', 'img_paths'] # Для проверки на пустоту позже

            for rel_path, type_key in items_to_remove:
                # Удаляем из списка в command_data (без try)
                if type_key in command_data and isinstance(command_data[type_key], list) and rel_path in command_data[type_key]:
                    command_data[type_key].remove(rel_path)
                    something_removed = True

                # Удаляем физически с диска (без try)
                path_abs = subfolder_abs / rel_path
                if path_abs.exists():
                     if path_abs.is_dir():
                         shutil.rmtree(path_abs) # Может вызвать ошибку
                     else:
                         path_abs.unlink() # Может вызвать ошибку
                     # Если rmtree/unlink не вызовут исключение, считаем удаление успешным
                else:
                     # _show_warning_mixin(self, "Предупреждение", f"Ресурс не найден на диске: {path_abs}")
                     # Не считаем это ошибкой, влияющей на общее сообщение
                     pass

            # Если что-то было удалено из списков команды
            if something_removed:
                # Проверяем, остались ли вообще какие-либо прикрепленные файлы/папки
                is_subfolder_empty = not any(command_data.get(k) for k in types_map_keys)

                # Если списки пусты И папка на диске существует
                if is_subfolder_empty and subfolder_abs.is_dir():
                    # Проверяем, пуста ли папка физически
                    # (может содержать что-то не связанное с командой)
                    if not any(subfolder_abs.iterdir()):
                         shutil.rmtree(subfolder_abs); # Удаляем пустую папку (без try)
                         command_data['subfolder'] = None # Убираем ссылку из команды
                    else:
                         # _show_warning_mixin(self, "Предупреждение", f"Субфолдер '{subfolder_abs}' не пуст и не будет удален.")
                         pass # Не удаляем непустую папку

                # Сохраняем изменения в tasks.json (без try)
                self.task_manager.save_tasks()
                # Вызываем функцию для обновления UI (включая скрытие секции, если надо)
                self._post_removal_update(command_manager_idx, folder_key, parent_dialog)

                # Сообщение пользователю (общее)
                if not error_occurred: # Если при удалении файлов не было ошибок
                    QMessageBox.information(self, "Удалено", "Выбранные ресурсы удалены.")
                # else: # Если были ошибки, менеджер должен был их показать
                #     QMessageBox.warning(self, "Завершено с ошибками", "Некоторые ресурсы не удалось удалить с диска.")

    def _post_removal_update(self, command_manager_idx, folder_key, parent_dialog):
        # Эта функция вызывается ПОСЛЕ удаления и сохранения в _remove_selected_attachments

        # Обновляем главный список команд в основном окне
        self._update_command_list()
        # Если диалог редактирования команды открыт, обновляем его секцию файлов
        if parent_dialog and parent_dialog.isVisible():
            # Находим фрейм и список
            files_frame = parent_dialog.findChild(QFrame, "filesSectionFrame")
            files_list = parent_dialog.attached_files_list_widget  # Используем сохраненную ссылку

            if files_frame and files_list:
                # Получаем (возможно) обновленные данные команды
                commands_list = self.task_manager.useful_commands.get(folder_key, [])
                # Минимальная проверка индекса
                if isinstance(commands_list, list) and 0 <= command_manager_idx < len(commands_list):
                    command_data = commands_list[command_manager_idx]
                    # Перезаполняем список файлов
                    parent_dialog.attached_files_paths_map = self._populate_attached_files(command_data, files_list)

                    # --- Управляем видимостью и кнопками ---
                    has_items = files_list.count() > 0 and "Нет прикрепленных" not in files_list.item(0).text()
                    files_frame.setVisible(has_items)  # Скрываем фрейм, если он пуст
                    files_list.setEnabled(has_items)  # Блокируем список, если пуст

                    # Обновляем состояние кнопок
                    view_btn = files_frame.findChild(QPushButton, "viewAttachedButton")
                    remove_btn = files_frame.findChild(QPushButton, "removeAttachedButton")
                    if view_btn: view_btn.setEnabled(has_items)
                    if remove_btn: remove_btn.setEnabled(has_items)
                    # --- Конец обновления UI в диалоге ---
                else:
                    # Команды больше нет? Скрываем секцию на всякий случай
                    files_frame.setVisible(False)
                    files_list.setEnabled(False)
                    view_btn = files_frame.findChild(QPushButton, "viewAttachedButton")
                    remove_btn = files_frame.findChild(QPushButton, "removeAttachedButton")
                    if view_btn: view_btn.setEnabled(False)
                    if remove_btn: remove_btn.setEnabled(False)
            else:
                # logging.warning("Не удалось найти files_frame или files_list в _post_removal_update.")
                pass  # Не нашли виджеты

    def go_back(self):
        if self.current_folder != 'root':
            self.current_folder = '/'.join(self.current_folder.split('/')[:-1]) or 'root'
            self._update_command_list()

    def open_folder_or_edit_command(self, item):
        if not item: return
        item_text = item.text()
        if item_text.startswith("[Папка]"):
            folder_key_to_open = item.data(Qt.UserRole)
            if not folder_key_to_open:
                folder_name = item_text[7:].strip()
                folder_key_to_open = folder_name if self.current_folder == 'root' else f"{self.current_folder}/{folder_name}"

            if folder_key_to_open in self.task_manager.useful_commands:
                self.current_folder = folder_key_to_open
                self._update_command_list()
            else:
                _show_warning_mixin(self, "Ошибка", f"Папка '{folder_key_to_open}' не найдена.")
                self._update_command_list()
        else:
            self.edit_command_description(item)