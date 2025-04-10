# START OF FILE google_drive.py

import datetime
import pickle
import io
import time
import webbrowser
import zipfile
import shutil
from pathlib import Path
import logging
import os

from PySide6.QtWidgets import QInputDialog, QMessageBox, QLineEdit
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from .utils import _show_warning_mixin, _show_critical_mixin

SCOPES = ["https://www.googleapis.com/auth/drive.appdata"]
CLIENT_CONFIG = {
    "installed": {
        "client_id": "622051045501-n5k5qqfuvtr7ndvjd4lr4q89ghjel4e4.apps.googleusercontent.com",
        "client_secret": "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",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob"]
    }
}
ARCHIVE_NAME = "tasks_folder_archive.zip"


class GoogleDriveMixin:

    def _get_settings_folder(self):
        settings_folder = Path("C:/TaskManagerSettings")
        settings_folder.mkdir(exist_ok=True)
        return settings_folder

    def _get_token_file(self):
        return self._get_settings_folder() / "google_token.pickle"

    def check_google_auth_status(self):
        token_file = self._get_token_file()
        creds = None
        if token_file.exists():
            try:
                with token_file.open("rb") as f:
                    creds = pickle.load(f)
            except Exception as e:
                try:
                    token_file.unlink(missing_ok=True)
                except OSError:
                    pass
                creds = None

        if creds and creds.valid:
            self.google_creds = creds
            self.update_google_auth_button()
            return True
        elif creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with token_file.open("wb") as f:
                    pickle.dump(creds, f)
                self.google_creds = creds
                self.update_google_auth_button()
                return True
            except Exception as e:
                if token_file.exists(): token_file.unlink(missing_ok=True)
                self.google_creds = None
                self.update_google_auth_button()
                _show_warning_mixin(self, "Ошибка Google",
                                    f"Не удалось обновить сеанс Google. Попробуйте войти снова.\n{e}")
                return False
        else:
            if creds:
                if token_file.exists(): token_file.unlink(missing_ok=True)
            self.google_creds = None
            self.update_google_auth_button()
            return False

    def update_google_auth_button(self):
        pass

    def toggle_google_auth(self):
        token_file = self._get_token_file()
        self.check_google_auth_status()

        if self.google_creds:
            if token_file.exists():
                try:
                    token_file.unlink()
                except OSError as e:
                    pass
            self.google_creds = None
            self.update_google_auth_button()
            QMessageBox.information(self, "Google Drive", "Вы вышли из аккаунта Google.")
        else:
            try:
                flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
                flow.redirect_uri = CLIENT_CONFIG['installed']['redirect_uris'][0]

                auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
                if not webbrowser.open(auth_url):
                    _show_warning_mixin(self, "Авторизация Google",
                                        f"Не удалось автоматически открыть браузер. Пожалуйста, откройте ссылку вручную:\n\n{auth_url}")

                code, ok = QInputDialog.getText(self, "Код авторизации Google",
                                                "Пожалуйста, скопируйте код со страницы авторизации Google и вставьте его сюда:",
                                                QLineEdit.Normal)
                if ok and code:
                    flow.fetch_token(code=code.strip())
                    creds = flow.credentials
                    token_file.parent.mkdir(exist_ok=True)
                    with token_file.open("wb") as f:
                        pickle.dump(creds, f)
                    self.google_creds = creds
                    self.update_google_auth_button()
                    QMessageBox.information(self, "Google Drive", "Авторизация через Google прошла успешно.")
                else:
                    QMessageBox.warning(self, "Google Drive", "Авторизация отменена или код не введен.")

            except Exception as e:
                _show_critical_mixin(self, "Ошибка авторизации Google", f"Не удалось авторизоваться: {str(e)}")
                if token_file.exists(): token_file.unlink(missing_ok=True)
                self.google_creds = None
                self.update_google_auth_button()

    def _remove_file_with_retries(self, file_path, max_attempts=5, delay=1):
        file_path = Path(file_path)
        if not file_path.exists():
            return True
        for attempt in range(max_attempts):
            try:
                if file_path.is_dir():
                    shutil.rmtree(file_path)
                else:
                    file_path.unlink()
                return True
            except OSError as e:
                if attempt == max_attempts - 1:
                    _show_warning_mixin(self, "Ошибка удаления",
                                        f"Не удалось удалить '{file_path.name}':\n{e}\n\nВозможно, файл используется другим процессом.")
                    return False
                time.sleep(delay)
        return False

    def upload_to_google_manual(self):
        if not self.check_google_auth_status():
            QMessageBox.warning(self, "Google Drive", "Сначала войдите через Google.")
            return False

        try:
            self.task_manager.save_tasks()
        except Exception as e:
            _show_critical_mixin(self, "Ошибка выгрузки", f"Ошибка сохранения данных перед выгрузкой:\n{e}")
            return False

        if not self.task_manager.check_tasks_file_exists():
            _show_warning_mixin(self, "Ошибка выгрузки", "Файл задач не найден. Выгрузка невозможна.")
            return False

        tasks_folder = self.tasks_file.parent
        parent_folder = tasks_folder.parent
        archive_path = parent_folder / ARCHIVE_NAME

        if not self._remove_file_with_retries(archive_path):
            return False

        try:
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for item in tasks_folder.iterdir():
                    if item.resolve() != archive_path.resolve():
                        if item.is_dir():
                            for root, _, files in os.walk(item):
                                for file in files:
                                    file_path_abs = Path(root) / file
                                    arcname = file_path_abs.relative_to(tasks_folder)
                                    zipf.write(file_path_abs, arcname)
                        elif item.is_file():
                            arcname = item.relative_to(tasks_folder)
                            zipf.write(item, arcname)
        except Exception as e:
            _show_critical_mixin(self, "Ошибка выгрузки", f"Ошибка создания архива '{archive_path.name}':\n{e}")
            self._remove_file_with_retries(archive_path)
            return False

        try:
            creds = self.google_creds
            service = build("drive", "v3", credentials=creds, cache_discovery=False)

            query = f"name='{ARCHIVE_NAME}' and trashed=false"
            results = service.files().list(q=query, spaces="appDataFolder", fields="files(id, name)").execute()
            files_found = results.get("files", [])
            for file_drive in files_found:
                try:
                    service.files().delete(fileId=file_drive["id"]).execute()
                except Exception as del_e:
                    _show_warning_mixin(self, "Предупреждение",
                                        f"Не удалось удалить предыдущую версию архива на Google Drive:\n{del_e}")

            file_metadata = {"name": archive_path.name, "parents": ["appDataFolder"]}

            # Остальной код создания запроса остается тем же:
            media = MediaFileUpload(str(archive_path), resumable=True)
            request = service.files().create(body=file_metadata, media_body=media, fields="id")
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    pass # прогресс здесь показывался в логе, теперь ничего

            QMessageBox.information(self, "Google Drive", "Архив успешно загружен на Google Диск!")
            return True

        except Exception as e:
            _show_critical_mixin(self, "Ошибка выгрузки", f"Ошибка загрузки на Google Диск:\n{e}")
            return False
        finally:
            self._remove_file_with_retries(archive_path)

    def download_from_google_auto(self):
        if not self.check_google_auth_status():
            QMessageBox.warning(self, "Google Drive", "Сначала войдите через Google.")
            return False

        tasks_folder = self.tasks_file.parent
        temp_folder = tasks_folder.parent
        temp_archive_path = temp_folder / f"{ARCHIVE_NAME}.download"

        backup_folder = temp_folder / f"{tasks_folder.name}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.copytree(tasks_folder, backup_folder, dirs_exist_ok=True, ignore_errors=True)
        except Exception as e:
            msg = f"Ошибка создания резервной копии: {e}. Продолжить загрузку?"
            if QMessageBox.warning(None, "Ошибка бэкапа", msg, QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No) == QMessageBox.No:
                return False

        download_ok = False
        critical_error = False
        try:
            creds = self.google_creds
            service = build("drive", "v3", credentials=creds, cache_discovery=False)

            query = f"name='{ARCHIVE_NAME}' and trashed=false"
            results = service.files().list(q=query, spaces="drive", fields="files(id, name)").execute()
            files = results.get("files", [])
            if not files:
                _show_warning_mixin(self, "Ошибка загрузки", f"Файл '{ARCHIVE_NAME}' не найден на Google Диске.")
                return False

            file_id = files[0]["id"]

            self._remove_file_with_retries(temp_archive_path)

            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status: pass # прогресс здесь показывался в логе, теперь ничего

            with temp_archive_path.open("wb") as f:
                fh.seek(0)
                f.write(fh.read())
            download_ok = True

            if not zipfile.is_zipfile(temp_archive_path):
                raise zipfile.BadZipFile(f"Скачанный файл '{temp_archive_path.name}' не является zip-архивом.")

            items_to_keep = {backup_folder.resolve()}
            if temp_archive_path.parent == tasks_folder: items_to_keep.add(
                temp_archive_path.resolve())
            for item in tasks_folder.iterdir():
                if item.resolve() not in items_to_keep:
                    if not self._remove_file_with_retries(item):
                        raise OSError(f"Не удалось очистить папку задач перед распаковкой (проблема с '{item.name}').")

            with zipfile.ZipFile(temp_archive_path, 'r') as zipf:
                zipf.extractall(tasks_folder)

            self.task_manager.load_tasks()
            self.update_task_lists()
            QMessageBox.information(self, "Google Drive", "Данные успешно скачаны и распакованы!")
            return True

        except zipfile.BadZipFile as e:
            _show_critical_mixin(self, "Ошибка загрузки",
                                 f"Скачанный архив поврежден или имеет неверный формат.\n{e}\n\nВосстановление из резервной копии...")
            critical_error = True
            return False
        except Exception as e:
            _show_critical_mixin(self, "Ошибка загрузки",
                                 f"Ошибка скачивания или распаковки:\n{e}\n\nВосстановление из резервной копии...")
            critical_error = True
            return False
        finally:
            if download_ok:
                self._remove_file_with_retries(temp_archive_path)
            if critical_error:
                if hasattr(self.task_manager, '_restore_from_backup'):
                    if self.task_manager._restore_from_backup(backup_folder):
                        self.update_task_lists()
                else:
                    _show_critical_mixin(self, "Ошибка восстановления",
                                         "Не удалось выполнить автоматическое восстановление.")
            elif download_ok and not critical_error and backup_folder.exists():
                self._remove_file_with_retries(backup_folder)
            elif backup_folder.exists():
                pass # Оставляем бэкап