import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

# --- Конфигурация ---
# Эти данные понадобятся для интеграции с Telethon
API_ID = 23883645
API_HASH = 'd14551e03adb7251eabff4dab1d9004d'
SESSION_NAME = 'anon'

def main():
    """
    Основная функция для запуска GUI приложения.
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
