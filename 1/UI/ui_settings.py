# UI/ui_settings.py
from . import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QApplication,
    QDialog, QTabWidget, QWidget, QLayout, QTextEdit,
    QRect, QPropertyAnimation, QEvent, QObject, QStyle
)

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справка по приложению 'Задачник'")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml(
            """
            <h2>Добро пожаловать в 'Задачник'!</h2>
            <p>Это приложение помогает эффективно управлять задачами и командами.</p>

            <h3>Основные функции:</h3>
            <ul>
                <li><b>Задачи</b>
                    <ul>
                        <li>Добавление: Кнопка <i>"Добавить задачу"</i>.</li>
                        <li>Редактирование: Двойной щелчок по задаче.</li>
                        <li>Статус/Приоритет: Контекстное меню (правый клик).</li>
                    </ul>
                </li>
                <li><b>Выполненные задачи</b>
                    <ul>
                        <li>Просмотр: Список завершенных задач.</li>
                        <li>Удаление: Удаление ненужных задач.</li>
                    </ul>
                </li>
                <li><b>Команды</b>
                    <ul>
                        <li>Создание: Связывайте файлы (.ino, .py, .pdf, изображения).</li>
                        <li>Поиск: Фильтруйте по имени.</li>
                        <li>Редактирование/Просмотр: Двойной щелчок.</li>
                        <li>Перемещение: Используйте Drag and Drop для перемещения команд между папками.</li>
                    </ul>
                </li>
                <li><b>Поиск</b>
                    <ul>
                        <li>Строки поиска: Вверху вкладок "Задачи" и "Команды".</li>
                    </ul>
                </li>
                <li><b>Настройки</b>
                    <ul>
                        <li>Панель настроек: Значок папки.</li>
                        <li>Темы, папка задач, экспорт/импорт, Google Drive.</li>
                    </ul>
                </li>
            </ul>

            <p><b>Совет:</b> Наведите курсор на элементы для подсказок. Экспериментируйте для освоения!</p>
            <p><b>Поддержка:</b> Если у вас есть вопросы, предложения или замечания, пожалуйста, свяжитесь с разработчиком.</p>
            """
        )
        layout.addWidget(help_text)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumSize(500, 400)
        self.parent = parent  # Ссылка на TaskApp для доступа к методам
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Вкладка "Общие настройки"
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        general_buttons = [
            ("Сменить тему", self.parent.toggle_theme, "Переключение между тёмной и светлой темой"),
            ("Сменить папку задач", self.parent.change_tasks_folder, "Выбор новой папки для хранения задач"),
            ("Экспорт", self.parent.export_tasks, "Сохранение задач и файлов в выбранную папку"),
            ("Импорт", self.parent.import_tasks, "Загрузка задач и файлов из выбранной папки")
        ]
        for text, callback, tooltip in general_buttons:
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            general_layout.addWidget(btn)
        general_layout.addStretch()
        self.tabs.addTab(general_tab, "Общие")

        # Кнопка закрытия
        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

class SettingsUI(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.is_animating = False
        self.settings_panel = None
        self.settings_toggle_button = None
        self.google_auth_button = None
        self.animation = None
        self.setup_settings_ui()

    def setup_settings_ui(self):
        # Настройка выдвижной панели
        self.settings_panel = QFrame(self.parent)
        self.settings_panel.setObjectName("settingsPanel")
        self.settings_panel.setFixedWidth(300)
        self.settings_panel.setGeometry(-300, 0, 300, self.parent.height())
        self.settings_panel.setVisible(False)
        settings_layout = QVBoxLayout(self.settings_panel)

        settings_buttons = [
            ("Загрузить на Google.Диск", self.parent.upload_to_google_manual, "Загрузка архива задач на Google Drive"),
            ("Скачать с Google.Диска", self.parent.download_from_google_auto, "Скачивание задач с Google Drive"),
            ("Справка", self.parent.show_help, "Открыть справку по использованию приложения"),
            ("Настройки", self.parent.open_settings_dialog, "Открыть дополнительные настройки")
        ]
        for text, callback, tooltip in settings_buttons:
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.clicked.connect(callback)
            btn.setMinimumHeight(40)
            btn.setStyleSheet("padding: 10px; font-size: 14px;")
            settings_layout.addWidget(btn)

        self.google_auth_button = QPushButton()
        self.google_auth_button.setToolTip("Вход или выход из Google аккаунта для работы с Drive")
        self.google_auth_button.setMinimumHeight(40)
        self.google_auth_button.setStyleSheet("padding: 10px; font-size: 14px;")
        self.update_google_auth_button()
        self.google_auth_button.clicked.connect(self.parent.toggle_google_auth)
        settings_layout.addWidget(self.google_auth_button)
        settings_layout.addStretch()

        # Кнопка для открытия/закрытия панели настроек
        left_layout = QHBoxLayout()
        self.settings_toggle_button = QPushButton()
        self.settings_toggle_button.setIcon(self.parent.style().standardIcon(QStyle.SP_DirIcon))
        self.settings_toggle_button.setFixedSize(40, 40)
        self.settings_toggle_button.setToolTip("Открыть/закрыть панель настроек")
        self.settings_toggle_button.clicked.connect(self.toggle_settings_panel)
        left_layout.addWidget(self.settings_toggle_button)
        left_layout.addStretch()

        # Добавляем left_layout в основной layout родителя
        self.parent.content_layout.addLayout(left_layout)

        # Устанавливаем фильтр событий
        QApplication.instance().installEventFilter(self)

    def update_google_auth_button(self):
        if self.parent.google_creds and self.parent.google_creds.valid:
            self.google_auth_button.setText("Выйти")
        else:
            self.google_auth_button.setText("Войти через Google")

    def toggle_settings_panel(self):
        if self.is_animating:
            return
        self.is_animating = True
        if self.settings_panel.isVisible():
            self.animation = QPropertyAnimation(self.settings_panel, b"geometry")
            self.animation.setDuration(300)
            self.animation.setStartValue(QRect(0, 0, 300, self.parent.height()))
            self.animation.setEndValue(QRect(-300, 0, 300, self.parent.height()))
            self.animation.finished.connect(lambda: self.settings_panel.setVisible(False))
            self.animation.finished.connect(lambda: setattr(self, 'is_animating', False))
            self.animation.start()
        else:
            self.settings_panel.setVisible(True)
            self.settings_panel.raise_()
            self.animation = QPropertyAnimation(self.settings_panel, b"geometry")
            self.animation.setDuration(300)
            self.animation.setStartValue(QRect(-300, 0, 300, self.parent.height()))
            self.animation.setEndValue(QRect(0, 0, 300, self.parent.height()))
            self.animation.finished.connect(lambda: setattr(self, 'is_animating', False))
            self.animation.start()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and self.settings_panel.isVisible() and not self.is_animating:
            click_pos = event.globalPos()
            panel_rect = self.settings_panel.geometry()
            panel_top_left = self.settings_panel.mapToGlobal(panel_rect.topLeft())
            panel_bottom_right = self.settings_panel.mapToGlobal(panel_rect.bottomRight())
            panel_rect_global = QRect(panel_top_left, panel_bottom_right)

            if not panel_rect_global.contains(click_pos):
                self.toggle_settings_panel()
                return True
            else:
                pass
        return False