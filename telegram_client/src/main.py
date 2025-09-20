import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

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
