BASE_STYLE = """
    QWidget {
        font-family: "Inter", "Roboto", "Segoe UI", Arial, sans-serif;
        font-size: 14px;
        font-weight: 400;
    }
    QTabWidget::pane, QListWidget, QDialog, QFrame#settingsPanel {
        border: none;
        border-radius: 8px;
    }
    QTabBar::tab {
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 14px;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 2px;
    }
    QListWidget::item {
        padding: 12px;
        border-radius: 6px;
        margin: 2px 0;
    }
    QPushButton {
        border: none;
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: 600;
        font-size: 14px;
        transition: background-color 0.2s ease, transform 0.1s ease;
    }
    QPushButton:hover {
        transform: scale(1.02);
    }
    QPushButton:pressed {
        transform: scale(0.98);
    }
    QLineEdit, QTextEdit {
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px;
        font-size: 15px;  /* Увеличиваем для лучшей читаемости */
        line-height: 1.5;  /* Улучшает читаемость текста */
    }
    QLineEdit:focus, QTextEdit:focus {
        border: 1px solid;
    }
    QComboBox {
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 10px;
        font-size: 14px;
    }
    QComboBox::drop-down {
        border: none;
        width: 24px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }
    QComboBox QAbstractItemView {
        border: none;
        border-radius: 8px;
        padding: 4px;
    }
    QCheckBox {
        font-size: 14px;
        padding: 6px;
    }
    QCheckBox::indicator {
        width: 20px;
        height: 20px;
        border-radius: 6px;
        border: 1px solid;
    }
    QCheckBox::indicator:checked {
        image: url(:/icons/check.png);
    }
    QScrollBar:vertical {
        border: none;
        width: 8px;
        margin: 0;
        background: transparent;
    }
    QScrollBar::handle:vertical {
        border-radius: 4px;
        min-height: 20px;
        transition: background-color 0.2s ease;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
        background: transparent;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: transparent;
    }
    QScrollBar:horizontal {
        border: none;
        height: 8px;
        margin: 0;
        background: transparent;
    }
    QScrollBar::handle:horizontal {
        border-radius: 4px;
        min-width: 20px;
        transition: background-color 0.2s ease;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
        background: transparent;
    }
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
        background: transparent;
    }
"""

THEMES = {
    "Dark": BASE_STYLE + """
        QWidget {
            background: #1A1B26;
            color: #D9E0EE;
        }
        QTabWidget::pane {
            background: #24283B;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        QTabBar::tab {
            background: #24283B;
            color: #A6ADC8;
        }
        QTabBar::tab:selected {
            background: #7AA2F7;
            color: #FFFFFF;
        }
        QTabBar::tab:hover:!selected {
            background: #414868;
            color: #D9E0EE;
        }
        QListWidget {
            background: #24283B;
            color: #D9E0EE;
            padding: 8px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        QListWidget::item {
            background: #2A2E45;
        }
        QListWidget::item:selected {
            background: #414868;
            color: #FFFFFF;
        }
        QListWidget::item:alternate {
            background: #2E334E;
        }
        QListWidget::item:hover {
            background: #414868;
            color: #FFFFFF;
        }
        QPushButton {
            background: #7AA2F7;
            color: #FFFFFF;
        }
        QPushButton:hover {
            background: #9AB8FF;
        }
        QPushButton:pressed {
            background: #5A85DB;
        }
        QLineEdit, QTextEdit {
            background: #2A2E45;
            color: #D9E0EE;
            border-color: #414868;
        }
        QTextEdit {
            padding: 12px;  /* Увеличенный отступ для справки */
            background: #2E334E;  /* Чуть светлее для выделения */
            border-radius: 10px;
            box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.2);  /* Лёгкая тень для глубины */
        }
        QLineEdit:focus, QTextEdit:focus {
            background: #2E334E;
            border-color: #7AA2F7;
            box-shadow: 0 0 4px rgba(122, 162, 247, 0.5);
        }
        QComboBox {
            background: #2A2E45;
            color: #D9E0EE;
            border-color: #414868;
        }
        QComboBox:hover {
            background: #414868;
        }
        QComboBox::drop-down {
            background: #414868;
        }
        QComboBox QAbstractItemView {
            background: #24283B;
            color: #D9E0EE;
            selection-background-color: #414868;
        }
        QCheckBox {
            color: #D9E0EE;
        }
        QCheckBox::indicator {
            border-color: #414868;
            background: #2A2E45;
        }
        QCheckBox::indicator:checked {
            background: #7AA2F7;
            border-color: #7AA2F7;
            image: url(:/icons/check-dark.png);
        }
        QCheckBox::indicator:hover {
            border-color: #9AB8FF;
        }
        QDialog {
            background: #1A1B26;
            color: #D9E0EE;
        }
        QFrame#settingsPanel {
            background: #24283B;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #414868;
        }
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background: #7AA2F7;
        }
        QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {
            background: #5A85DB;
        }
    """,
    "Light": BASE_STYLE + """
        QWidget {
            background: #F5F7FA;
            color: #1F2A44;
        }
        QTabWidget::pane {
            background: #FFFFFF;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        QTabBar::tab {
            background: #E5E7EB;
            color: #6B7280;
        }
        QTabBar::tab:selected {
            background: #3B82F6;
            color: #FFFFFF;
        }
        QTabBar::tab:hover:!selected {
            background: #D1D5DB;
            color: #1F2A44;
        }
        QListWidget {
            background: #FFFFFF;
            color: #1F2A44;
            padding: 8px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        QListWidget::item {
            background: #F9FAFB;
        }
        QListWidget::item:selected {
            background: #E5E7EB;
            color: #1F2A44;
        }
        QListWidget::item:alternate {
            background: #F1F3F5;
        }
        QListWidget::item:hover {
            background: #E5E7EB;
            color: #1F2A44;
        }
        QPushButton {
            background: #3B82F6;
            color: #FFFFFF;
        }
        QPushButton:hover {
            background: #60A5FA;
        }
        QPushButton:pressed {
            background: #2563EB;
        }
        QLineEdit, QTextEdit {
            background: #FFFFFF;
            color: #1F2A44;
            border-color: #D1D5DB;
        }
        QTextEdit {
            padding: 12px;  /* Увеличенный отступ для справки */
            background: #F9FAFB;  /* Чуть темнее для выделения */
            border-radius: 10px;
            box-shadow: inset 0 1px 4px rgba(0, 0, 0, 0.05);  /* Лёгкая тень для глубины */
        }
        QLineEdit:focus, QTextEdit:focus {
            background: #F9FAFB;
            border-color: #3B82F6;
            box-shadow: 0 0 4px rgba(59, 130, 246, 0.5);
        }
        QComboBox {
            background: #FFFFFF;
            color: #1F2A44;
            border-color: #D1D5DB;
        }
        QComboBox:hover {
            background: #E5E7EB;
        }
        QComboBox::drop-down {
            background: #E5E7EB;
        }
        QComboBox QAbstractItemView {
            background: #FFFFFF;
            color: #1F2A44;
            selection-background-color: #E5E7EB;
        }
        QCheckBox {
            color: #1F2A44;
        }
        QCheckBox::indicator {
            border-color: #D1D5DB;
            background: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background: #3B82F6;
            border-color: #3B82F6;
            image: url(:/icons/check-light.png);
        }
        QCheckBox::indicator:hover {
            border-color: #60A5FA;
        }
        QDialog {
            background: #F5F7FA;
            color: #1F2A44;
        }
        QFrame#settingsPanel {
            background: #FFFFFF;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
            background: #D1D5DB;
        }
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
            background: #3B82F6;
        }
        QScrollBar::handle:vertical:pressed, QScrollBar::handle:horizontal:pressed {
            background: #2563EB;
        }
    """
}