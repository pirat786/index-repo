# UI/__init__.py
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QListWidget, QListWidgetItem, QVBoxLayout, QHBoxLayout,
    QPushButton, QInputDialog, QMessageBox, QLineEdit, QDialog, QTextEdit, QLabel,
    QFileDialog, QMenu, QDialogButtonBox, QCheckBox, QStyle, QFrame, QApplication, QLayout,
)
from PySide6.QtCore import Qt, QUrl, QTimer, QRect, QPropertyAnimation, QEvent, QObject,QMimeData
from PySide6.QtGui import QBrush, QColor, QFont, QDesktopServices, QIcon, QDrag

from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from pathlib import Path
import json
import logging
import os
import shutil
import zipfile
import pickle
import io
import time
import webbrowser

from styles.styles import THEMES
from cods.task_manager import (
    TaskManager, SETTINGS_FOLDER, SETTINGS_FILE, CURRENT_VERSION, _save_json, _load_json
)
from cods.dialogs import SortDialog

from .dialogs import FolderSelectionDialog
from .task_management import TaskManagementMixin
from .command_management import CommandManagementMixin
from .google_drive import GoogleDriveMixin
from .settings_and_themes import SettingsAndThemesMixin
from .export_import import ExportImportMixin
from .utils import ListUpdateMixin
from .ui_settings import SettingsUI, SettingsDialog, HelpDialog