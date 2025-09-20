import sys
from PyQt6.QtCore import QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog
)
from telethon_client import TelethonClient

import re

class MainWindow(QMainWindow):
    """
    Главное окно приложения.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Client")
        self.setGeometry(100, 100, 800, 600)
        self.all_chats = []
        self.init_ui()
        self.init_telethon_thread()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel_layout = QVBoxLayout()
        chat_list_label = QLabel("Выберите исходный чат:")
        self.chat_list_widget = QListWidget()
        self.chat_list_widget.setAccessibleName("Список чатов")
        self.chat_list_widget.itemClicked.connect(self.on_chat_selected)
        left_panel_layout.addWidget(chat_list_label)
        left_panel_layout.addWidget(self.chat_list_widget)

        right_panel_layout = QVBoxLayout()
        controls_layout = QVBoxLayout()

        source_chat_label = QLabel("Исходный чат:")
        self.source_chat_input = QLineEdit()
        self.source_chat_input.setReadOnly(True)
        self.source_chat_input.setAccessibleName("Выбранный исходный чат")

        dest_chat_label = QLabel("Целевой чат (введите ID):")
        self.dest_chat_input = QLineEdit()
        self.dest_chat_input.setAccessibleName("Поле ввода для ID целевого чата")

        self.count_button = QPushButton("Подсчитать сообщения")
        self.count_button.clicked.connect(self.on_count_button_clicked)
        self.export_txt_button = QPushButton("Экспорт в .txt")
        self.export_txt_button.clicked.connect(self.on_export_txt_clicked)
        self.export_zip_button = QPushButton("Экспорт в .zip")
        self.export_zip_button.clicked.connect(self.on_export_zip_clicked)
        self.forward_all_button = QPushButton("Переслать все сообщения")
        self.forward_all_button.clicked.connect(self.on_forward_all_clicked)

        controls_layout.addWidget(source_chat_label)
        controls_layout.addWidget(self.source_chat_input)
        controls_layout.addWidget(dest_chat_label)
        controls_layout.addWidget(self.dest_chat_input)
        controls_layout.addWidget(self.count_button)
        controls_layout.addWidget(self.export_txt_button)
        controls_layout.addWidget(self.export_zip_button)
        controls_layout.addWidget(self.forward_all_button)

        log_label = QLabel("Логи и статус:")
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setAccessibleName("Логи выполнения операций")

        right_panel_layout.addLayout(controls_layout)
        right_panel_layout.addWidget(log_label)
        right_panel_layout.addWidget(self.log_widget)

        main_layout.addLayout(left_panel_layout, 1)
        main_layout.addLayout(right_panel_layout, 2)

        self.setStatusBar(QStatusBar(self))
        self.log("Приложение запущено.")

    def init_telethon_thread(self):
        self.telethon_thread = QThread()
        self.telethon_client = TelethonClient()
        self.telethon_client.moveToThread(self.telethon_thread)

        self.telethon_thread.started.connect(self.telethon_client.start_connecting) # Обновленное имя метода
        self.telethon_client.dialogs_ready.connect(self.update_chat_list)
        self.telethon_client.status_update.connect(self.log)
        self.telethon_client.message_count_ready.connect(self.on_message_count_ready)
        self.telethon_client.export_finished.connect(self.on_export_finished)
        self.telethon_client.forwarding_finished.connect(self.on_forwarding_finished)
        self.telethon_thread.finished.connect(self.telethon_thread.deleteLater)

        self.telethon_thread.start()

    @pyqtSlot(str)
    def log(self, message):
        self.log_widget.append(message)
        self.statusBar().showMessage(message)
        print(message)

    @pyqtSlot(list)
    def update_chat_list(self, chats):
        self.log(f"Получено {len(chats)} чатов. Обновление списка...")
        self.all_chats = chats
        self.chat_list_widget.clear()
        for chat in chats:
            self.chat_list_widget.addItem(chat['name'])
        self.log("Список чатов обновлен.")

    @pyqtSlot(QListWidgetItem)
    def on_chat_selected(self, item):
        selected_chat_name = item.text()
        chat_data = next((chat for chat in self.all_chats if chat['name'] == selected_chat_name), None)
        if chat_data:
            self.source_chat_input.setText(f"{chat_data['name']} (ID: {chat_data['id']})")
            self.log(f"Выбран исходный чат: {chat_data['name']}")

    @pyqtSlot()
    def on_count_button_clicked(self):
        """Слот для кнопки подсчета сообщений."""
        source_text = self.source_chat_input.text()
        if not source_text:
            self.log("Ошибка: Исходный чат не выбран.")
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return

        # Извлекаем ID из текста "Chat Name (ID: 12345)"
        match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not match:
            self.log(f"Ошибка: Не удалось извлечь ID из строки '{source_text}'")
            return

        chat_id = int(match.group(1))
        self.log(f"Запускаем подсчет сообщений для чата ID: {chat_id}")
        self.telethon_client.start_message_count(chat_id)

    @pyqtSlot(int)
    def on_message_count_ready(self, count):
        """Слот для отображения результата подсчета сообщений."""
        source_text = self.source_chat_input.text()
        self.log(f"Результат получен: в чате '{source_text}' найдено {count} сообщений.")
        QMessageBox.information(self, "Результат подсчета", f"В чате '{source_text}'\nВсего сообщений: {count}")

    def closeEvent(self, event):
        self.log("Завершение работы...")
        if self.telethon_thread.isRunning():
            self.telethon_thread.quit()
            self.telethon_thread.wait()
        event.accept()

    @pyqtSlot()
    def on_export_txt_clicked(self):
        """Слот для кнопки экспорта в .txt."""
        source_text = self.source_chat_input.text()
        if not source_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return

        match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not match:
            self.log(f"Ошибка: Не удалось извлечь ID из строки '{source_text}'")
            return

        chat_id = int(match.group(1))

        # Предлагаем имя файла по умолчанию
        default_filename = f"chat_{chat_id}_export.txt"

        # Открываем диалог сохранения файла
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить экспорт чата", default_filename, "Text Files (*.txt);;All Files (*)")

        if filepath:
            self.log(f"Запускаем экспорт чата ID {chat_id} в файл {filepath}")
            self.telethon_client.start_export_to_txt(chat_id, filepath)

    @pyqtSlot(str)
    def on_export_finished(self, filepath):
        """Слот для обработки завершения экспорта."""
        self.log(f"Экспорт в файл {filepath} успешно завершен.")
        QMessageBox.information(self, "Экспорт завершен", f"История чата была успешно сохранена в файл:\n{filepath}")

    @pyqtSlot()
    def on_export_zip_clicked(self):
        """Слот для кнопки экспорта в .zip."""
        source_text = self.source_chat_input.text()
        if not source_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return

        match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not match:
            self.log(f"Ошибка: Не удалось извлечь ID из строки '{source_text}'")
            return

        chat_id = int(match.group(1))

        default_filename = f"chat_{chat_id}_export.zip"
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить ZIP-архив", default_filename, "ZIP Archives (*.zip);;All Files (*)")

        if filepath:
            self.log(f"Запускаем экспорт чата ID {chat_id} в ZIP-архив {filepath}")
            self.telethon_client.start_export_to_zip(chat_id, filepath)

    @pyqtSlot()
    def on_forward_all_clicked(self):
        """Слот для кнопки пересылки всех сообщений."""
        source_text = self.source_chat_input.text()
        dest_text = self.dest_chat_input.text()

        if not source_text or not dest_text:
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать исходный чат и указать ID целевого чата.")
            return

        source_match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not source_match:
            self.log(f"Ошибка: Не удалось извлечь ID из строки исходного чата '{source_text}'")
            return

        try:
            source_chat_id = int(source_match.group(1))
            dest_chat_id = int(dest_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "ID целевого чата должен быть числом.")
            return

        self.log(f"Запускаем пересылку из {source_chat_id} в {dest_chat_id}")
        self.telethon_client.start_forwarding_all(source_chat_id, dest_chat_id)

    @pyqtSlot(int)
    def on_forwarding_finished(self, count):
        """Слот для обработки завершения пересылки."""
        self.log(f"Пересылка успешно завершена. Всего переслано {count} сообщений.")
        QMessageBox.information(self, "Пересылка завершена", f"Всего было переслано {count} сообщений.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
