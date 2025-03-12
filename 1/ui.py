#UI.py
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QLineEdit, QDialog, QTextEdit, QLabel,
    QFileDialog, QMenu, QFrame, QComboBox, QApplication, QDialogButtonBox, QCheckBox
)
import json
import logging
from PySide6.QtGui import QBrush, QColor, QFont, QIcon
from PySide6.QtCore import Qt, QRect, QPropertyAnimation, QEvent
from PySide6.QtWidgets import QStyle
from styles import THEMES
from task_manager import TaskManager, SETTINGS_FOLDER, SETTINGS_FILE
from dialogs import SortDialog
import webbrowser
import zipfile
import os
import shutil
import pickle
import io
import time  # Убедитесь, что импортирован в начале файла
import psutil  # Опционально, для анализа процессов (установите: pip install psutil)
import gc  # Для принудительной сборки мусора
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
from google.auth.transport.requests import Request

logging.basicConfig(level=logging.INFO)


class FolderSelectionDialog(QDialog):
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выбор дополнительных папок")
        self.folder_path = folder_path
        self.selected_folders = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Выберите дополнительные папки с .py файлами для включения:"))

        subfolders = [f for f in os.listdir(self.folder_path)
                      if os.path.isdir(os.path.join(self.folder_path, f))]
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


class TaskApp(QWidget):
    def __init__(self, tasks_file):  # Принимаем tasks_file как аргумент
        super().__init__()
        self.tasks_file = tasks_file  # Сохраняем tasks_file как атрибут
        self.task_manager = TaskManager(tasks_file)
        self.current_theme = self.load_theme()
        self.google_creds = None  # Храним объект Credentials для Google
        self.setWindowTitle("Задачник")
        self.setGeometry(100, 100, 800, 600)
        self.init_ui()
        self.update_task_lists()
        self.check_google_auth_status()  # Проверяем статус авторизации при запуске

    def load_theme(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    return settings.get('theme', 'Dark')
            return 'Dark'
        except Exception:
            return 'Dark'

    def save_theme(self, theme):
        try:
            settings = {
                'theme': theme,
                'tasks_folder': os.path.dirname(self.tasks_file)
            }
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            logging.info(f"Настройки сохранены в {SETTINGS_FILE}")
        except Exception as e:
            logging.error(f"Ошибка сохранения настроек: {e}")

    def change_tasks_folder(self):
        """Изменяет папку для хранения задач без перемещения существующих данных"""
        new_folder = QFileDialog.getExistingDirectory(self, "Выберите новую папку для хранения задач",
                                                      os.path.dirname(self.tasks_file))
        if new_folder:
            try:
                # Убедимся, что новая папка существует
                os.makedirs(new_folder, exist_ok=True)

                # Обновляем путь к tasks_file, не перемещая файлы
                self.tasks_file = os.path.abspath(os.path.join(new_folder, "tasks.json"))

                # Создаём новый экземпляр TaskManager с новым tasks_file
                self.task_manager = TaskManager(self.tasks_file)

                # Обновляем список задач
                self.update_task_lists()

                # Сохраняем новую папку и тему в настройках
                self.save_theme(self.current_theme)

                # Сохраняем текущий токен Google, если он существует
                if self.google_creds:
                    token_file = SETTINGS_FILE.replace('.json', '.pickle')
                    try:
                        os.makedirs(os.path.dirname(token_file), exist_ok=True)
                        with open(token_file, "wb") as token_file:
                            pickle.dump(self.google_creds, token_file)
                        logging.info(f"Токен Google сохранён в {token_file} при смене папки")
                    except Exception as e:
                        logging.error(f"Ошибка сохранения токена Google при смене папки: {str(e)}")

                QMessageBox.information(self, "Успех", f"Папка задач изменена на {new_folder}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось изменить папку: {str(e)}")
                logging.error(f"Ошибка изменения папки: {str(e)}")
            if self.settings_panel.isVisible():
                self.toggle_settings_panel()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.settings_panel = QFrame(self)
        self.settings_panel.setObjectName("settingsPanel")
        self.settings_panel.setFixedWidth(250)
        self.settings_panel.setGeometry(-215, 0, 215, self.height())
        self.settings_panel.setVisible(False)
        settings_layout = QVBoxLayout(self.settings_panel)

        for text, callback in [
            ("Сменить тему", self.toggle_theme),
            ("Сменить папку "
             "задач", self.change_tasks_folder),
            ("Экспорт", self.export_tasks),
            ("Импорт", self.import_tasks),
            ("Загрузить на "
             "Google.Диск", self.upload_to_google_manual),
            ("Скачать с "
             "Google.Диска", self.download_from_google_auto)
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            settings_layout.addWidget(btn)

        # Добавляем кнопку для Google авторизации
        self.google_auth_button = QPushButton()
        self.update_google_auth_button()  # Устанавливаем начальное состояние кнопки
        self.google_auth_button.clicked.connect(self.toggle_google_auth)
        settings_layout.addWidget(self.google_auth_button)

        settings_layout.addStretch()

        left_layout = QHBoxLayout()
        self.settings_toggle_button = QPushButton()
        self.settings_toggle_button.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.settings_toggle_button.setFixedSize(40, 40)
        self.settings_toggle_button.clicked.connect(self.toggle_settings_panel)
        left_layout.addWidget(self.settings_toggle_button)
        left_layout.addStretch()

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.addLayout(left_layout)
        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)

        self.pending_tab, self.task_list_widget = self._create_tab("Задачи")
        self.completed_tab, self.completed_task_list_widget = self._create_tab("Выполненные задачи")
        self.commands_tab, self.command_list_widget = self._create_tab("Команды")

        self.search_bar = QLineEdit(placeholderText="Поиск задач...")
        self.search_bar.textChanged.connect(self.filter_tasks)
        self.pending_tab.layout().insertWidget(0, self.search_bar)

        button_layout = QHBoxLayout()
        for text, callback in [("Добавить задачу", self.add_task), ("Удалить задачу", self.delete_task),
                               ("Сортировать", self.open_sort_dialog)]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        self.pending_tab.layout().addLayout(button_layout)

        completed_button_layout = QHBoxLayout()
        for text, callback in [("Удалить задачу", self.delete_task), ("Сортировать", self.open_sort_dialog)]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            completed_button_layout.addWidget(btn)
        self.completed_tab.layout().addLayout(completed_button_layout)

        command_button_layout = QHBoxLayout()
        for text, callback in [
            ("Добавить команду", self.add_command),
            ("Удалить команду", self.delete_command),
            ("Сортировать", self.sort_commands),
            ("Прикрепить .ino/папку", self.attach_ino_file)
        ]:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            command_button_layout.addWidget(btn)
        self.commands_tab.layout().addLayout(command_button_layout)

        main_layout.addWidget(content_widget)
        self.apply_theme()

        content_widget.installEventFilter(self)

    def check_google_auth_status(self):
        """Проверяет, существует ли и действителен токен Google"""
        token_file = SETTINGS_FILE.replace('.json', '.pickle')  # Используем .pickle для токена
        if os.path.exists(token_file):
            try:
                with open(token_file, "rb") as token_file:
                    creds = pickle.load(token_file)
                logging.info(f"Токен успешно загружен из {token_file}")
                logging.debug(f"Refresh Token: {creds.refresh_token}")
                logging.debug(f"Access Token: {creds.token is not None}")
                logging.debug(f"Token expiry: {creds.expiry}")
                if creds and creds.valid:
                    self.google_creds = creds
                    self.update_google_auth_button()
                    return True
                elif creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        with open(token_file, "wb") as token_file:
                            pickle.dump(creds, token_file)
                        logging.info(f"Токен обновлён и сохранён в {token_file}")
                        self.google_creds = creds
                        self.update_google_auth_button()
                        return True
                    except Exception as e:
                        logging.error(f"Не удалось обновить токен: {str(e)}. Требуется повторная авторизация.")
                        QMessageBox.warning(self, "Ошибка",
                                            f"Не удалось обновить токен: {str(e)}. Пожалуйста, войдите заново.")
                        self.google_creds = None
                        self.update_google_auth_button()
                        return False
                else:
                    logging.warning("Токен недействителен или отсутствует Refresh Token")
                    self.google_creds = None
                    self.update_google_auth_button()
                    return False
            except (pickle.UnpicklingError, EOFError, ValueError) as e:
                logging.error(f"Ошибка проверки токена: {str(e)}. Токен повреждён или в неверном формате.")
                QMessageBox.warning(self, "Ошибка", f"Токен повреждён: {str(e)}. Требуется повторная авторизация.")
                self.google_creds = None
                self.update_google_auth_button()
                return False
            except Exception as e:
                logging.error(f"Ошибка проверки токена: {str(e)}")
                QMessageBox.warning(self, "Ошибка", f"Не удалось проверить токен: {str(e)}")
                self.google_creds = None
                self.update_google_auth_button()
                return False
        self.google_creds = None
        self.update_google_auth_button()
        logging.info("Токен не найден, требуется авторизация")
        return False

    def update_google_auth_button(self):
        """Обновляет текст и иконку кнопки Google в зависимости от статуса авторизации"""
        if self.google_creds and self.google_creds.valid:
            self.google_auth_button.setText("Выйти")
            # Можно установить иконку выхода (пример, если у вас есть иконка)
            self.google_auth_button.setIcon(QIcon("path/to/logout_icon.png"))  # Замените на путь к иконке выхода
        else:
            self.google_auth_button.setText("Войти через Google")
            # Можно установить иконку Google (пример, если у вас есть иконка)
            self.google_auth_button.setIcon(QIcon("path/to/google_icon.png"))  # Замените на путь к иконке Google

    def toggle_google_auth(self):
        """Обрабатывает вход или выход из Google аккаунта"""
        if self.google_creds and self.google_creds.valid:
            # Выход — удаляем токен
            token_file = SETTINGS_FILE.replace('.json', '.pickle')
            if os.path.exists(token_file):
                try:
                    os.remove(token_file)
                    self.google_creds = None
                    logging.info(f"Токен удалён из {token_file}")
                    QMessageBox.information(self, "Успех", "Вы вышли из Google аккаунта.")
                    self.update_google_auth_button()
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить токен: {str(e)}")
                    logging.error(f"Ошибка удаления токена: {str(e)}")
            else:
                self.google_creds = None
                self.update_google_auth_button()
        else:
            # Вход — запрашиваем авторизацию
            SCOPES = ["https://www.googleapis.com/auth/drive.file"]
            client_config = {
                "installed": {
                    "client_id": "user",
                    "client_secret": "user",
                    "auth_uri": "user",
                    "token_uri": "user",
                    "auth_provider_x509_cert_url": "user",
                    "redirect_uris": ["user"]
                }
            }

            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            flow.redirect_uri = "user"
            auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
            webbrowser.open(auth_url)
            code, ok = QInputDialog.getText(self, "Код авторизации",
                                            "Скопируйте код с открывшейся страницы Google и вставьте сюда:")
            if ok and code:
                try:
                    flow.fetch_token(code=code)
                    creds = flow.credentials
                    token_file = SETTINGS_FILE.replace('.json', '.pickle')
                    try:
                        os.makedirs(os.path.dirname(token_file), exist_ok=True)
                        logging.info(f"Папка для токена {os.path.dirname(token_file)} создана или уже существует")
                    except PermissionError as e:
                        QMessageBox.warning(self, "Ошибка",
                                            f"Нет прав доступа к {os.path.dirname(token_file)}: {str(e)}")
                        logging.error(f"Нет прав доступа к {os.path.dirname(token_file)}: {str(e)}")
                        return
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка",
                                            f"Не удалось создать папку для токена {os.path.dirname(token_file)}: {str(e)}")
                        logging.error(f"Ошибка создания папки для токена {os.path.dirname(token_file)}: {str(e)}")
                        return

                    try:
                        with open(token_file, "wb") as token_file:
                            pickle.dump(creds, token_file)
                        self.google_creds = creds
                        logging.info(f"Токен успешно сохранён в {token_file}")
                        logging.debug(f"Refresh Token: {creds.refresh_token}")
                        logging.debug(f"Access Token: {creds.token is not None}")
                        logging.debug(f"Token expiry: {creds.expiry}")
                        QMessageBox.information(self, "Успех", "Вы успешно вошли через Google.")
                        self.update_google_auth_button()
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить токен: {str(e)}")
                        logging.error(f"Ошибка сохранения токена: {str(e)}")
                        return
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось получить токен: {str(e)}")
                    logging.error(f"Ошибка получения токена: {str(e)}")
                    return
            else:
                QMessageBox.warning(self, "Ошибка", "Код авторизации не введён")

    def upload_to_google_manual(self):
        """Ручная загрузка на Google Диск с явным redirect_uri"""
        if not self.check_google_auth_status():
            QMessageBox.warning(self, "Ошибка", "Сначала войдите через Google.")
            return

        self.task_manager.save_tasks()
        if self.task_manager.check_tasks_file_exists():
            tasks_folder = os.path.dirname(self.tasks_file)
            parent_folder = os.path.dirname(tasks_folder)
            archive_name = os.path.join(parent_folder, "tasks_folder_archive.zip")

            # Удаляем существующий архив, если он есть, с повторными попытками
            if os.path.exists(archive_name):
                max_attempts = 5  # Увеличиваем количество попыток до 5
                delay = 2  # Увеличиваем задержку до 2 секунд
                for attempt in range(max_attempts):
                    try:
                        os.remove(archive_name)
                        logging.info(f"Локальный архив {archive_name} удалён перед созданием нового")
                        break
                    except WindowsError as e:
                        if e.winerror == 32:  # Error 32: File is in use
                            logging.warning(
                                f"Попытка {attempt + 1}/{max_attempts}: Файл {archive_name} занят другим процессом. Ждём {delay} секунд...")
                            time.sleep(delay)
                            try:
                                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                                    for file in proc.open_files():
                                        if archive_name.lower() in file.path.lower():
                                            logging.error(
                                                f"Файл {archive_name} заблокирован процессом {proc.name()} (PID: {proc.pid}, Команда: {proc.cmdline()})")
                                            QMessageBox.warning(self, "Предупреждение",
                                                                f"Не удалось удалить локальный архив {archive_name} автоматически: файл заблокирован процессом {proc.name()} (PID: {proc.pid}). Закройте процесс или удалите файл вручную.")
                            except Exception as pe:
                                logging.error(f"Не удалось определить процесс, блокирующий файл: {str(pe)}")
                            if attempt == max_attempts - 1:
                                QMessageBox.warning(self, "Предупреждение",
                                                    f"Не удалось удалить локальный архив {archive_name} автоматически: {str(e)}. Удалите файл вручную.")
                                logging.error(
                                    f"Не удалось удалить локальный архив {archive_name} автоматически: {str(e)}")
                                return
                        else:
                            raise

            try:
                # Архивируем только содержимое tasks_folder, без самой папки
                zipf = zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED)
                try:
                    for root, dirs, files in os.walk(tasks_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Вычисляем путь относительно tasks_folder, чтобы избежать дублирования папки
                            arcname = os.path.relpath(file_path, tasks_folder)
                            zipf.write(file_path, arcname)
                    logging.info(f"Архив {archive_name} успешно создан")
                finally:
                    zipf.close()  # Явное закрытие zipf
                    gc.collect()  # Принудительная сборка мусора для освобождения ресурсов
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось создать архив: {str(e)}")
                logging.error(f"Ошибка создания архива: {str(e)}")
                return

            creds = self.google_creds
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        token_file = SETTINGS_FILE.replace('.json', '.pickle')
                        with open(token_file, "wb") as token_file:
                            pickle.dump(creds, token_file)
                        logging.info("Токен успешно обновлён через Refresh Token")
                        logging.info(f"Обновлённый токен сохранён в {token_file}")
                    except Exception as e:
                        QMessageBox.warning(self, "Ошибка", f"Не удалось обновить токен: {str(e)}")
                        logging.error(f"Ошибка обновления токена: {str(e)}")
                        self.google_creds = None
                        self.update_google_auth_button()
                        return
                else:
                    QMessageBox.warning(self, "Ошибка", "Срок действия токена истёк. Войдите заново через Google.")
                    self.google_creds = None
                    self.update_google_auth_button()
                    return

            # Удаляем старый архив на Google Диске, если он существует
            try:
                service = build("drive", "v3", credentials=creds, cache_discovery=False)
                # Ищем существующий файл tasks_folder_archive.zip
                results = service.files().list(
                    q="name='tasks_folder_archive.zip'",
                    spaces="drive",
                    fields="files(id, name)"
                ).execute()
                files = results.get("files", [])

                if files:
                    for file in files:
                        service.files().delete(fileId=file["id"]).execute()
                        logging.info(f"Удалён старый архив с ID {file['id']} на Google Диске")
            except Exception as e:
                logging.warning(f"Не удалось удалить старый архив на Google Диске: {str(e)}")

            # Загружаем новый архив
            try:
                service = build("drive", "v3", credentials=creds, cache_discovery=False)
                file_metadata = {"name": "tasks_folder_archive.zip"}
                media = MediaFileUpload(archive_name)
                service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                QMessageBox.information(self, "Успех", "Архив успешно загружен на Google Диск!")
                logging.info("Архив успешно загружен на Google Диск")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")
                logging.error(f"Ошибка загрузки на Google Диск: {str(e)}")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось сохранить файл tasks.json.")

    def download_from_google_auto(self):
        """Автоматическое скачивание архива с Google Диска с использованием OAuth"""
        if not self.check_google_auth_status():
            QMessageBox.warning(self, "Ошибка", "Сначала войдите через Google.")
            return

        try:
            os.makedirs(SETTINGS_FOLDER, exist_ok=True)
            logging.info(f"Папка {SETTINGS_FOLDER} создана или уже существует")
        except PermissionError as e:
            QMessageBox.warning(self, "Ошибка", f"Нет прав доступа к {SETTINGS_FOLDER}: {str(e)}")
            logging.error(f"Нет прав доступа к {SETTINGS_FOLDER}: {str(e)}")
            return
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать папку {SETTINGS_FOLDER}: {str(e)}")
            logging.error(f"Ошибка создания папки {SETTINGS_FOLDER}: {str(e)}")
            return

        SCOPES = ["https://www.googleapis.com/auth/drive.file"]
        client_config = {
            "installed": {
                "client_id": "user",
                "client_secret": "user",
                "auth_uri": "user",
                "token_uri": "user",
                "auth_provider_x509_cert_url": "user",
                "redirect_uris": ["user"]
            }
        }

        creds = self.google_creds
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    token_file = SETTINGS_FILE.replace('.json', '.pickle')
                    with open(token_file, "wb") as token_file:
                        pickle.dump(creds, token_file)
                    logging.info("Токен успешно обновлён через Refresh Token")
                    logging.info(f"Обновлённый токен сохранён в {token_file}")
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось обновить токен: {str(e)}")
                    logging.error(f"Ошибка обновления токена: {str(e)}")
                    self.google_creds = None
                    self.update_google_auth_button()
                    return
            else:
                QMessageBox.warning(self, "Ошибка", "Срок действия токена истёк. Войдите заново через Google.")
                self.google_creds = None
                self.update_google_auth_button()
                return

        try:
            service = build("drive", "v3", credentials=creds, cache_discovery=False)
            results = service.files().list(
                q="name='tasks_folder_archive.zip'",
                spaces="drive",
                fields="files(id, name)"
            ).execute()
            files = results.get("files", [])

            if not files:
                QMessageBox.warning(self, "Ошибка", "Файл tasks_folder_archive.zip не найден на Google Диске")
                logging.warning("Файл tasks_folder_archive.zip не найден на Google Диске")
                return

            file_id = files[0]["id"]
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

            tasks_folder = os.path.dirname(self.tasks_file)
            temp_archive = os.path.join(tasks_folder, "tasks_folder_archive.zip")

            # Убедимся, что старый архив удалён перед скачиванием нового, с повторными попытками
            if os.path.exists(temp_archive):
                max_attempts = 5  # Увеличиваем количество попыток
                delay = 2  # Увеличиваем задержку до 2 секунд
                for attempt in range(max_attempts):
                    try:
                        os.remove(temp_archive)
                        logging.info(f"Локальный архив {temp_archive} удалён перед скачиванием")
                        break
                    except WindowsError as e:
                        if e.winerror == 32:  # Error 32: File is in use
                            logging.warning(
                                f"Попытка {attempt + 1}/{max_attempts}: Файл {temp_archive} занят другим процессом. Ждём {delay} секунд...")
                            time.sleep(delay)
                            if attempt == max_attempts - 1:
                                # Пытаемся найти процесс, блокирующий файл (опционально, с psutil)
                                try:
                                    for proc in psutil.process_iter(['pid', 'name']):
                                        for file in proc.open_files():
                                            if temp_archive.lower() in file.path.lower():
                                                logging.error(
                                                    f"Файл {temp_archive} заблокирован процессом {proc.name()} (PID: {proc.pid})")
                                                QMessageBox.warning(self, "Предупреждение",
                                                                    f"Не удалось удалить локальный архив {temp_archive} автоматически: файл заблокирован процессом {proc.name()}. Закройте процесс или удалите файл вручную.")
                                except Exception as pe:
                                    logging.error(f"Не удалось определить процесс, блокирующий файл: {str(pe)}")
                                QMessageBox.warning(self, "Предупреждение",
                                                    f"Не удалось удалить локальный архив {temp_archive} автоматически: {str(e)}. Удалите файл вручную.")
                                logging.error(
                                    f"Не удалось удалить локальный архив {temp_archive} автоматически: {str(e)}")
                                return
                        else:
                            raise

            with open(temp_archive, "wb") as f:
                fh.seek(0)
                f.write(fh.read())

            for item in os.listdir(tasks_folder):
                item_path = os.path.join(tasks_folder, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif os.path.isfile(item_path) and item_path != temp_archive:
                    os.remove(item_path)

            with zipfile.ZipFile(temp_archive, 'r') as zipf:
                zipf.extractall(tasks_folder)

            # Удаляем временный архив после распаковки с повторными попытками
            max_attempts = 5
            delay = 2
            for attempt in range(max_attempts):
                try:
                    os.remove(temp_archive)
                    logging.info(f"Временный архив {temp_archive} удалён после распаковки")
                    break
                except WindowsError as e:
                    if e.winerror == 32:  # Error 32: File is in use
                        logging.warning(
                            f"Попытка {attempt + 1}/{max_attempts}: Файл {temp_archive} занят другим процессом. Ждём {delay} секунд...")
                        time.sleep(delay)
                        if attempt == max_attempts - 1:
                            try:
                                for proc in psutil.process_iter(['pid', 'name']):
                                    for file in proc.open_files():
                                        if temp_archive.lower() in file.path.lower():
                                            logging.error(
                                                f"Файл {temp_archive} заблокирован процессом {proc.name()} (PID: {proc.pid})")
                                            QMessageBox.warning(self, "Предупреждение",
                                                                f"Не удалось удалить временный архив {temp_archive} автоматически: файл заблокирован процессом {proc.name()}. Закройте процесс или удалите файл вручную.")
                            except Exception as pe:
                                logging.error(f"Не удалось определить процесс, блокирующий файл: {str(pe)}")
                            QMessageBox.warning(self, "Предупреждение",
                                                f"Не удалось удалить временный архив {temp_archive} автоматически: {str(e)}. Удалите файл вручную.")
                            logging.error(f"Не удалось удалить временный архив {temp_archive} автоматически: {str(e)}")
                    else:
                        raise

            self.task_manager.load_tasks()
            self.update_task_lists()
            QMessageBox.information(self, "Успех", "Данные успешно скачаны и распакованы с Google Диска!")
            logging.info("Данные успешно скачаны и распакованы")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось скачать файл: {str(e)}")
            logging.error(f"Ошибка скачивания файла: {str(e)}")

    def _create_tab(self, title):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        list_widget = QListWidget()
        list_widget.setAlternatingRowColors(True)
        list_widget.setFont(QFont("Arial", 14))
        list_widget.itemClicked.connect(self.highlight_task)
        list_widget.itemDoubleClicked.connect(
            self.edit_description if title != "Команды" else self.edit_command_description)
        if title != "Команды":
            list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
            list_widget.customContextMenuRequested.connect(self.show_context_menu)
        layout.addWidget(list_widget)
        self.tabs.addTab(tab, title)
        return tab, list_widget

    def apply_theme(self):
        self.setStyleSheet(THEMES[self.current_theme])
        self.update_task_lists()

    def toggle_theme(self):
        self.current_theme = "Light" if self.current_theme == "Dark" else "Dark"
        self.save_theme(self.current_theme)
        self.apply_theme()
        if self.settings_panel.isVisible():
            self.toggle_settings_panel()

    def toggle_settings_panel(self):
        if self.settings_panel.isVisible():
            self.animation = QPropertyAnimation(self.settings_panel, b"geometry")
            self.animation.setDuration(300)
            self.animation.setStartValue(QRect(0, 0, 215, self.height()))
            self.animation.setEndValue(QRect(-215, 0, 215, self.height()))
            self.animation.finished.connect(lambda: self.settings_panel.setVisible(False))
            self.animation.start()
        else:
            self.settings_panel.setVisible(True)
            self.settings_panel.raise_()  # Поднимаем панель на передний план
            self.animation = QPropertyAnimation(self.settings_panel, b"geometry")
            self.animation.setDuration(300)
            self.animation.setStartValue(QRect(-215, 0, 215, self.height()))
            self.animation.setEndValue(QRect(0, 0, 215, self.height()))
            self.animation.start()

    def eventFilter(self, obj, event):
        """Фильтр событий для закрытия панели при клике вне её"""
        if obj == self.findChild(QWidget) and event.type() == QEvent.MouseButtonPress:
            if self.settings_panel.isVisible():
                # Проверяем, был ли клик вне панели настроек
                click_pos = event.globalPos()
                panel_rect = self.settings_panel.geometry()
                if not panel_rect.contains(self.mapToGlobal(self.mapFromGlobal(click_pos))):
                    self.toggle_settings_panel()
        return super().eventFilter(obj, event)

    def show_context_menu(self, pos):
        widget = self.sender()
        item = widget.itemAt(pos)
        if item:
            is_completed = widget == self.completed_task_list_widget
            idx = widget.row(item)
            menu = QMenu(self)

            status_menu = menu.addMenu("Изменить статус")
            for status in TaskManager.STATUS_OPTIONS:
                action = status_menu.addAction(status)
                action.triggered.connect(
                    lambda _, s=status, i=idx, c=is_completed: self.task_manager.change_status(i, s, c))
                action.triggered.connect(lambda: self.update_task_lists())

            priority_menu = menu.addMenu("Изменить приоритет")
            for priority in TaskManager.PRIORITY_LEVELS:
                action = priority_menu.addAction(priority)
                action.triggered.connect(lambda _, p=priority, i=idx, c=is_completed: self.change_priority(i, p, c))
                action.triggered.connect(lambda: self.update_task_lists())

            menu.exec(widget.mapToGlobal(pos))

    def change_priority(self, idx, priority, is_completed):
        self.task_manager.change_priority(idx, priority, is_completed)
        self._update_single_list(is_completed)

    def _darken_color(self, hex_color):
        color = QColor(hex_color)
        h, s, l, a = color.getHslF()
        return QColor.fromHslF(h, s, max(0, l - 0.1), a).name()

    def highlight_task(self, item):
        item.setSelected(True)

    def edit_description(self, item):
        is_completed = item.listWidget() == self.completed_task_list_widget
        idx = item.listWidget().row(item)
        task_list = self.task_manager.completed_tasks if is_completed else self.task_manager.pending_tasks
        task = task_list[idx]
        self._edit_item(task, idx, is_task=True, is_completed=is_completed)

    def edit_command_description(self, item):
        idx = self.command_list_widget.row(item)
        command = self.task_manager.useful_commands[idx]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование: {command['name']}")
        layout = QVBoxLayout(dialog)

        name_edit = QLineEdit(command['name'])
        layout.addWidget(name_edit)

        desc_edit = QTextEdit()
        desc_edit.setPlainText(command['description'])
        layout.addWidget(desc_edit)

        ino_path = command.get('ino_path', None)
        subfolder = command.get('subfolder', '')
        if isinstance(ino_path, str):
            ino_label = QLabel(f"Прикрепленный файл: {ino_path}")
            layout.addWidget(ino_label)
        elif isinstance(ino_path, list):
            ino_label = QLabel(f"Прикрепленные файлы: {', '.join(ino_path) if ino_path else 'Нет'}")
            layout.addWidget(ino_label)
        else:
            ino_label = QLabel("Прикрепленные файлы: Нет")
            layout.addWidget(ino_label)

        if ino_path:
            view_button = QPushButton("Просмотреть файл")
            view_button.clicked.connect(lambda: self._select_and_view_file(subfolder, ino_path))
            layout.addWidget(view_button)

        attach_button = QPushButton("Изменить/Прикрепить .ino/папку")
        attach_button.clicked.connect(lambda: self._update_ino_file(idx, dialog))
        layout.addWidget(attach_button)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(
            lambda: self._save_item_changes(dialog, command, name_edit, desc_edit, idx, False, False))
        layout.addWidget(save_button)

        dialog.setMinimumSize(600, 400)
        dialog.exec()

    def _select_and_view_file(self, subfolder, ino_path):
        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите файл для просмотра")
        layout = QVBoxLayout(dialog)

        file_selector = QComboBox()
        if isinstance(ino_path, str):
            file_selector.addItem(ino_path)
        elif isinstance(ino_path, list):
            file_selector.addItems(ino_path)
        layout.addWidget(file_selector)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(lambda: self.view_ino_file(
            os.path.join(os.path.dirname(self.tasks_file), subfolder, file_selector.currentText())))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.exec()

    def _edit_item(self, item, idx, is_task=True, is_completed=False):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование: {item['name']}")
        layout = QVBoxLayout(dialog)

        name_edit = QLineEdit(item['name'])
        layout.addWidget(name_edit)

        if is_task:
            time_info = f"Создано: {item.get('created_time', 'N/A')}\nНачало: {item.get('started_time', 'N/A')}\nВыполнено: {item.get('completed_time', 'N/A')}"
            time_label = QLabel(time_info)
            time_label.setFont(QFont("Arial", 10))
            time_label.setMinimumHeight(60)
            layout.addWidget(time_label)

        desc_edit = QTextEdit()
        desc_edit.setPlainText(item['description'])
        layout.addWidget(desc_edit)

        save_button = QPushButton("Сохранить")
        save_button.clicked.connect(
            lambda: self._save_item_changes(dialog, item, name_edit, desc_edit, idx, is_task, is_completed))
        layout.addWidget(save_button)

        dialog.setMinimumSize(600, 400)
        dialog.exec()

    def _save_item_changes(self, dialog, item, name_edit, desc_edit, idx, is_task, is_completed):
        item['name'] = name_edit.text()
        item['description'] = desc_edit.toPlainText()
        self.task_manager.update_description(idx, item['description'], is_task, is_completed)
        self._update_single_list(is_completed if is_task else None)
        dialog.accept()

    def add_task(self):
        name, ok = QInputDialog.getText(self, "Новая задача", "Введите название задачи:")
        if ok and name:
            priority, ok = QInputDialog.getItem(self, "Приоритет", "Выберите приоритет:", TaskManager.PRIORITY_LEVELS,
                                                1, False)
            if ok:
                self.task_manager.add_task(name, priority)
                self._update_single_list(False)

    def add_command(self):
        name, ok = QInputDialog.getText(self, "Новая команда", "Введите название команды:")
        if ok and name:
            attach_type, ok2 = QInputDialog.getItem(
                self,
                "Прикрепить файл или папку",
                "Что вы хотите прикрепить?",
                ["Ничего", "Файл .ino", "Папку с .py"],
                0,
                False
            )
            ino_path = None
            folder_path = None
            additional_folders = None
            if ok2:
                if attach_type == "Файл .ino":
                    ino_path, _ = QFileDialog.getOpenFileName(
                        self,
                        "Выберите .ino файл",
                        "",
                        "Arduino Files (*.ino);;All Files (*)"
                    )
                elif attach_type == "Папку с .py":
                    folder_path = QFileDialog.getExistingDirectory(
                        self,
                        "Выберите папку с .py файлами",
                        ""
                    )
                    if folder_path:
                        dialog = FolderSelectionDialog(folder_path, self)
                        if dialog.exec():
                            additional_folders = dialog.get_selected_folders()
            self.task_manager.add_command(name, ino_path, folder_path, additional_folders)
            self._update_single_list(None)

    def delete_task(self):
        selected_pending = self.task_list_widget.selectedItems()
        selected_completed = self.completed_task_list_widget.selectedItems()
        if selected_pending or selected_completed:
            if QMessageBox.question(self, "Удаление", "Удалить выбранные задачи?",
                                    QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                for item in selected_pending:
                    self.task_manager.delete_task(self.task_list_widget.row(item), False)
                for item in selected_completed:
                    self.task_manager.delete_task(self.completed_task_list_widget.row(item), True)
                self.update_task_lists()

    def delete_command(self):
        selected = self.command_list_widget.selectedItems()
        if selected and QMessageBox.question(self, "Удаление", "Удалить выбранные команды?",
                                             QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for item in selected:
                self.task_manager.delete_command(self.command_list_widget.row(item))
            self._update_single_list(None)

    def attach_ino_file(self):
        selected = self.command_list_widget.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите команду для прикрепления файла или папки!")
            return

        idx = self.command_list_widget.row(selected[0])
        attach_type, ok = QInputDialog.getItem(
            self,
            "Прикрепить файл или папку",
            "Что вы хотите прикрепить?",
            ["Файл .ino", "Папку с .py"],
            0,
            False
        )
        ino_path = None
        folder_path = None
        additional_folders = None
        if ok:
            if attach_type == "Файл .ino":
                ino_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Выберите .ino файл",
                    "",
                    "Arduino Files (*.ino);;All Files (*)"
                )
            elif attach_type == "Папку с .py":
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "Выберите папку с .py файлами",
                    ""
                )
                if folder_path:
                    dialog = FolderSelectionDialog(folder_path, self)
                    if dialog.exec():
                        additional_folders = dialog.get_selected_folders()
        if ino_path or folder_path:
            self.task_manager.update_command_ino(idx, ino_path, folder_path, additional_folders)
            self._update_single_list(None)
            QMessageBox.information(self, "Успех", f"Файлы успешно прикреплены к команде!")

    def view_ino_file(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Просмотр: {os.path.basename(file_path)}")
            layout = QVBoxLayout(dialog)
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setPlainText(content)
            layout.addWidget(text_edit)
            dialog.setMinimumSize(600, 400)
            dialog.exec()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть файл: {str(e)}")

    def _update_ino_file(self, idx, parent_dialog):
        attach_type, ok = QInputDialog.getItem(
            self,
            "Прикрепить файл или папку",
            "Что вы хотите прикрепить?",
            ["Файл .ino", "Папку с .py"],
            0,
            False
        )
        ino_path = None
        folder_path = None
        additional_folders = None
        if ok:
            if attach_type == "Файл .ino":
                ino_path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Выберите .ino файл",
                    "",
                    "Arduino Files (*.ino);;All Files (*)"
                )
            elif attach_type == "Папку с .py":
                folder_path = QFileDialog.getExistingDirectory(
                    self,
                    "Выберите папку с .py файлами",
                    ""
                )
                if folder_path:
                    dialog = FolderSelectionDialog(folder_path, self)
                    if dialog.exec():
                        additional_folders = dialog.get_selected_folders()
        if ino_path or folder_path:
            self.task_manager.update_command_ino(idx, ino_path, folder_path, additional_folders)
            self._update_single_list(None)
            parent_dialog.accept()

    def export_tasks(self):
        parent_dir = QFileDialog.getExistingDirectory(self, "Выберите родительскую папку для экспорта")
        if parent_dir:
            folder_name, ok = QInputDialog.getText(self, "Экспорт", "Введите имя папки для экспорта:")
            if ok and folder_name:
                folder_path = os.path.join(parent_dir, folder_name)
                success = self.task_manager.export_tasks(folder_path)
                if success:
                    QMessageBox.information(self, "Успех", f"Задачи успешно экспортированы в {folder_path}!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось экспортировать задачи.")
        if self.settings_panel.isVisible():
            self.toggle_settings_panel()

    def import_tasks(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выберите папку для импорта")
        if folder_path:
            success = self.task_manager.import_tasks(folder_path)
            if success:
                self.update_task_lists()
                QMessageBox.information(self, "Успех", "Задачи успешно импортированы!")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось импортировать задачи.")
        if self.settings_panel.isVisible():
            self.toggle_settings_panel()

    def open_sort_dialog(self):
        SortDialog(self.sort_tasks, self).exec()

    def sort_tasks(self, by='name'):
        self.task_manager.sort_tasks(by)
        self.update_task_lists()

    def sort_commands(self):
        self.task_manager.sort_commands()
        self._update_single_list(None)

    def filter_tasks(self, text):
        text = text.lower()
        self.task_list_widget.clear()
        self.completed_task_list_widget.clear()
        self.command_list_widget.clear()
        self._populate_list(self.task_list_widget,
                            [t for t in self.task_manager.pending_tasks if text in t['name'].lower()][:100])
        self._populate_list(self.completed_task_list_widget,
                            [t for t in self.task_manager.completed_tasks if text in t['name'].lower()][:100])
        self._populate_list(self.command_list_widget,
                            [c for c in self.task_manager.useful_commands if text in c['name'].lower()])

    def update_task_lists(self):
        self.task_list_widget.clear()
        self.completed_task_list_widget.clear()
        self.command_list_widget.clear()
        self._populate_list(self.task_list_widget, self.task_manager.pending_tasks[:100])
        self._populate_list(self.completed_task_list_widget, self.task_manager.completed_tasks[:100])
        self._populate_list(self.command_list_widget, self.task_manager.useful_commands)

    def _update_single_list(self, is_completed):
        if is_completed is None:
            self.command_list_widget.clear()
            self._populate_list(self.command_list_widget, self.task_manager.useful_commands)
        elif is_completed:
            self.completed_task_list_widget.clear()
            self._populate_list(self.completed_task_list_widget, self.task_manager.completed_tasks[:100])
        else:
            self.task_list_widget.clear()
            self._populate_list(self.task_list_widget, self.task_manager.pending_tasks[:100])

    def _populate_list(self, widget, items):
        status_colors = self.task_manager.STATUS_COLORS_LIGHT if self.current_theme == "Light" else self.task_manager.STATUS_COLORS_DARK
        for item in items:
            if 'status' in item:
                text = f"{item['name']} - {item['status']} (Приоритет: {item['priority']})"
                list_item = QListWidgetItem(text)
                list_item.setForeground(QBrush(QColor(status_colors.get(item['status'], "#FFFFFF"))))
                if item['priority'] == "Высокий":
                    list_item.setFont(QFont("Arial", 14, QFont.Bold))
            else:
                ino_path = item.get('ino_path')
                if isinstance(ino_path, str):
                    text = f"{item['name']} [ino]"
                elif isinstance(ino_path, list):
                    text = f"{item['name']} [py: {len(ino_path)}]"
                else:
                    text = f"{item['name']}"
                list_item = QListWidgetItem(text)
                list_item.setForeground(QBrush(QColor("#FFFFFF" if self.current_theme == "Dark" else "#333333")))
            widget.addItem(list_item)