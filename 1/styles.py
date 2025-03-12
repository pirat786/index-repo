THEMES = {
    "Dark": """
        /* Общий фон и текст */
        QWidget {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1E1F2E, stop:0.5 #2A2D42, stop:1 #1A1B26);
            color: #E0E7FF;
            font-family: "Inter", "Segoe UI", Arial, sans-serif;
            font-size: 14px;
        }

        /* Панель вкладок */
        QTabWidget::pane {
            border: 1px solid #3F435F;
            background: #2A2D42;
            border-radius: 14px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.05);
        }

        /* Вкладки */
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3F435F, stop:1 #2A2D42);
            border: 1px solid #3F435F;
            border-bottom: none;
            padding: 16px 28px;
            font: bold 14px;
            color: #B0B8D8;
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
            margin-right: 6px;
            transition: all 0.3s ease;
        }
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6D91FF, stop:1 #486EFF);
            border: 1px solid #6D91FF;
            color: #FFFFFF;
            border-bottom: none;
            box-shadow: 0 4px 14px rgba(109, 145, 255, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.15);
        }
        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #4A4E6D, stop:1 #3F435F);
            color: #E0E7FF;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        }

        /* Список задач */
        QListWidget {
            background: #2A2D42;
            border: 1px solid #3F435F;
            color: #E0E7FF;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25), inset 0 1px 2px rgba(255, 255, 255, 0.03);
        }
        QListWidget::item {
            padding: 14px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4A4E6D, stop:1 #3F435F);
            color: #FFFFFF;
            border: 1px solid #6D91FF;
            box-shadow: 0 3px 10px rgba(109, 145, 255, 0.4);
        }
        QListWidget::item:alternate {
            background: #31344E;
        }
        QListWidget::item:hover {
            background: #3F435F;
            color: #FFFFFF;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        }

        /* Кнопки */
        QPushButton {
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font: bold 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6D91FF, stop:1 #486EFF);
            color: #FFFFFF;
            box-shadow: 0 6px 16px rgba(109, 145, 255, 0.4), inset 0 1px 2px rgba(255, 255, 255, 0.15);
            transition: all 0.3s ease;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #8AAEFF, stop:1 #6D91FF);
            box-shadow: 0 8px 20px rgba(109, 145, 255, 0.5);
            transform: translateY(-2px);
        }
        QPushButton:pressed {
            background: #486EFF;
            box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.25);
            transform: translateY(2px);
        }

        /* Поле ввода */
        QLineEdit {
            background: #31344E;
            border: 1px solid #4A4E6D;
            border-radius: 10px;
            padding: 12px;
            color: #E0E7FF;
            font: 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.03);
            transition: all 0.3s ease;
        }
        QLineEdit:focus {
            border: 1px solid #6D91FF;
            background: #3F435F;
            box-shadow: 0 0 10px rgba(109, 145, 255, 0.6);
        }

        /* Текстовый редактор */
        QTextEdit {
            background: #31344E;
            border: 1px solid #4A4E6D;
            border-radius: 10px;
            padding: 12px;
            color: #E0E7FF;
            font: 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.03);
        }
        QTextEdit:focus {
            border: 1px solid #6D91FF;
            background: #3F435F;
            box-shadow: 0 0 10px rgba(109, 145, 255, 0.6);
        }

        /* Выпадающий список */
        QComboBox {
            background: #31344E;
            border: 1px solid #4A4E6D;
            border-radius: 10px;
            padding: 12px;
            color: #E0E7FF;
            font: 14px;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
        }
        QComboBox:hover {
            border: 1px solid #6D91FF;
            box-shadow: 0 4px 12px rgba(109, 145, 255, 0.3);
        }
        QComboBox::drop-down {
            border-left: 1px solid #4A4E6D;
            width: 28px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4A4E6D, stop:1 #3F435F);
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        }
        QComboBox QAbstractItemView {
            background: #2A2D42;
            color: #E0E7FF;
            border: 1px solid #3F435F;
            selection-background-color: #4A4E6D;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
        }

        /* Чекбоксы */
        QCheckBox {
            color: #E0E7FF;
            font: 14px;
            padding: 8px;
        }
        QCheckBox::indicator {
            width: 22px;
            height: 22px;
            border: 1px solid #4A4E6D;
            border-radius: 8px;
            background: #31344E;
            transition: all 0.3s ease;
        }
        QCheckBox::indicator:checked {
            background: #6D91FF;
            border: 1px solid #6D91FF;
            image: url(:/icons/check-dark.png); /* Предполагается наличие иконки */
            box-shadow: 0 2px 6px rgba(109, 145, 255, 0.4);
        }
        QCheckBox::indicator:hover {
            border: 1px solid #8AAEFF;
            box-shadow: 0 2px 6px rgba(109, 145, 255, 0.2);
        }

        /* Диалоговые окна */
        QDialog {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #1E1F2E, stop:0.5 #2A2D42, stop:1 #1A1B26);
            color: #E0E7FF;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
        }

        /* Панель настроек */
        QFrame#settingsPanel {
            background: #2A2D42;
            border: 1px solid #3F435F;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35), inset 0 1px 2px rgba(255, 255, 255, 0.05);
        }
    """,
    "Light": """
        /* Общий фон и текст */
        QWidget {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F4F7FB, stop:0.5 #EDEFF4, stop:1 #E6E9EF);
            color: #1C2A44;
            font-family: "Inter", "Segoe UI", Arial, sans-serif;
            font-size: 14px;
        }

        /* Панель вкладок */
        QTabWidget::pane {
            border: 1px solid #D1D9E6;
            background: #FFFFFF;
            border-radius: 14px;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1), inset 0 1px 2px rgba(255, 255, 255, 0.8);
        }

        /* Вкладки */
        QTabBar::tab {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #EDEFF4, stop:1 #DCE0E8);
            border: 1px solid #D1D9E6;
            border-bottom: none;
            padding: 16px 28px;
            font: bold 14px;
            color: #64748B;
            border-top-left-radius: 14px;
            border-top-right-radius: 14px;
            margin-right: 6px;
            transition: all 0.3s ease;
        }
        QTabBar::tab:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2DD4BF, stop:1 #0EA5E9);
            border: 1px solid #2DD4BF;
            color: #FFFFFF;
            border-bottom: none;
            box-shadow: 0 4px 14px rgba(45, 212, 191, 0.5), inset 0 1px 2px rgba(255, 255, 255, 0.2);
        }
        QTabBar::tab:hover:!selected {
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #F4F7FB, stop:1 #EDEFF4);
            color: #1C2A44;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
        }

        /* Список задач */
        QListWidget {
            background: #FFFFFF;
            border: 1px solid #D1D9E6;
            color: #1C2A44;
            border-radius: 12px;
            padding: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05), inset 0 1px 2px rgba(255, 255, 255, 0.8);
        }
        QListWidget::item {
            padding: 14px;
            border-radius: 10px;
            transition: all 0.3s ease;
        }
        QListWidget::item:selected {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EDEFF4, stop:1 #DCE0E8);
            color: #1C2A44;
            border: 1px solid #2DD4BF;
            box-shadow: 0 3px 10px rgba(45, 212, 191, 0.3);
        }
        QListWidget::item:alternate {
            background: #F9FAFC;
        }
        QListWidget::item:hover {
            background: #F4F7FB;
            color: #1C2A44;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
        }

        /* Кнопки */
        QPushButton {
            border: none;
            border-radius: 12px;
            padding: 14px 24px;
            font: bold 15px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2DD4BF, stop:1 #0EA5E9);
            color: #FFFFFF;
            box-shadow: 0 6px 16px rgba(45, 212, 191, 0.4), inset 0 1px 2px rgba(255, 255, 255, 0.2);
            transition: all 0.3s ease;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #5EEAD4, stop:1 #2DD4BF);
            box-shadow: 0 8px 20px rgba(45, 212, 191, 0.5);
            transform: translateY(-2px);
        }
        QPushButton:pressed {
            background: #0EA5E9;
            box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.2);
            transform: translateY(2px);
        }

        /* Поле ввода */
        QLineEdit {
            background: #FFFFFF;
            border: 1px solid #D1D9E6;
            border-radius: 10px;
            padding: 12px;
            color: #1C2A44;
            font: 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05), inset 0 1px 2px rgba(255, 255, 255, 0.8);
            transition: all 0.3s ease;
        }
        QLineEdit:focus {
            border: 1px solid #2DD4BF;
            background: #F9FAFC;
            box-shadow: 0 0 10px rgba(45, 212, 191, 0.6);
        }

        /* Текстовый редактор */
        QTextEdit {
            background: #FFFFFF;
            border: 1px solid #D1D9E6;
            border-radius: 10px;
            padding: 12px;
            color: #1C2A44;
            font: 14px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05), inset 0 1px 2px rgba(255, 255, 255, 0.8);
        }
        QTextEdit:focus {
            border: 1px solid #2DD4BF;
            background: #F9FAFC;
            box-shadow: 0 0 10px rgba(45, 212, 191, 0.6);
        }

        /* Выпадающий список */
        QComboBox {
            background: #FFFFFF;
            border: 1px solid #D1D9E6;
            border-radius: 10px;
            padding: 12px;
            color: #1C2A44;
            font: 14px;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.05);
        }
        QComboBox:hover {
            border: 1px solid #2DD4BF;
            box-shadow: 0 4px 12px rgba(45, 212, 191, 0.2);
        }
        QComboBox::drop-down {
            border-left: 1px solid #D1D9E6;
            width: 28px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #EDEFF4, stop:1 #DCE0E8);
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        }
        QComboBox QAbstractItemView {
            background: #FFFFFF;
            color: #1C2A44;
            border: 1px solid #D1D9E6;
            selection-background-color: #EDEFF4;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        }

        /* Чекбоксы */
        QCheckBox {
            color: #1C2A44;
            font: 14px;
            padding: 8px;
        }
        QCheckBox::indicator {
            width: 22px;
            height: 22px;
            border: 1px solid #D1D9E6;
            border-radius: 8px;
            background: #FFFFFF;
            transition: all 0.3s ease;
        }
        QCheckBox::indicator:checked {
            background: #2DD4BF;
            border: 1px solid #2DD4BF;
            image: url(:/icons/check-light.png); /* Предполагается наличие иконки */
            box-shadow: 0 2px 6px rgba(45, 212, 191, 0.4);
        }
        QCheckBox::indicator:hover {
            border: 1px solid #5EEAD4;
            box-shadow: 0 2px 6px rgba(45, 212, 191, 0.2);
        }

        /* Диалоговые окна */
        QDialog {
            background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F4F7FB, stop:0.5 #EDEFF4, stop:1 #E6E9EF);
            color: #1C2A44;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
        }

        /* Панель настроек */
        QFrame#settingsPanel {
            background: #FFFFFF;
            border: 1px solid #D1D9E6;
            border-radius: 14px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15), inset 0 1px 2px rgba(255, 255, 255, 0.8);
        }
    """
}