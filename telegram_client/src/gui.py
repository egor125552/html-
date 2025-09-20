import sys
import re
from PyQt6.QtCore import QThread, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QLineEdit, QTextEdit, QStatusBar,
    QMessageBox, QFileDialog, QInputDialog
)
from telethon_client import TelethonClient

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telegram Client")
        self.setGeometry(100, 100, 800, 600)
        self.all_chats = []
        self.init_ui()
        self.init_telethon_thread()

    def init_ui(self):
        # ... (UI setup is the same as before)
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

        # --- Соединяем все сигналы и слоты ---
        # Стандартные сигналы
        self.telethon_client.dialogs_ready.connect(self.update_chat_list)
        self.telethon_client.status_update.connect(self.log)
        self.telethon_client.message_count_ready.connect(self.on_message_count_ready)
        self.telethon_client.export_finished.connect(self.on_export_finished)
        self.telethon_client.forwarding_finished.connect(self.on_forwarding_finished)

        # Сигналы для входа
        self.telethon_client.phone_required.connect(self.prompt_for_phone)
        self.telethon_client.code_required.connect(self.prompt_for_code)
        self.telethon_client.password_required.connect(self.prompt_for_password)

        self.telethon_thread.finished.connect(self.telethon_thread.deleteLater)
        self.telethon_thread.started.connect(self.telethon_client.start_connecting)
        self.telethon_thread.start()

    # --- Слоты для входа ---
    @pyqtSlot()
    def prompt_for_phone(self):
        text, ok = QInputDialog.getText(self, 'Требуется номер телефона', 'Пожалуйста, введите ваш номер телефона:')
        if ok and text:
            self.telethon_client.send_phone(text)
        else:
            self.log("Ввод номера телефона отменен. Авторизация невозможна.")

    @pyqtSlot()
    def prompt_for_code(self):
        text, ok = QInputDialog.getText(self, 'Требуется код', 'Пожалуйста, введите код, полученный в Telegram:')
        if ok and text:
            self.telethon_client.send_code(text)
        else:
            self.log("Ввод кода отменен. Авторизация невозможна.")

    @pyqtSlot()
    def prompt_for_password(self):
        text, ok = QInputDialog.getText(self, 'Требуется пароль', 'Пожалуйста, введите ваш пароль (2FA):', QLineEdit.EchoMode.Password)
        if ok and text:
            self.telethon_client.send_password(text)
        else:
            self.log("Ввод пароля отменен. Авторизация невозможна.")

    # --- Остальные слоты ---
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
        source_text = self.source_chat_input.text()
        if not source_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return
        match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not match: return
        chat_id = int(match.group(1))
        self.telethon_client.start_message_count(chat_id)

    @pyqtSlot(int)
    def on_message_count_ready(self, count):
        source_text = self.source_chat_input.text()
        QMessageBox.information(self, "Результат подсчета", f"В чате '{source_text}'\nВсего сообщений: {count}")

    @pyqtSlot(str)
    def on_export_finished(self, filepath):
        QMessageBox.information(self, "Экспорт завершен", f"История чата была успешно сохранена в файл:\n{filepath}")

    @pyqtSlot()
    def on_export_txt_clicked(self):
        source_text = self.source_chat_input.text()
        if not source_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return
        match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not match: return
        chat_id = int(match.group(1))
        default_filename = f"chat_{chat_id}_export.txt"
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить экспорт чата", default_filename, "Text Files (*.txt);;All Files (*)")
        if filepath:
            self.telethon_client.start_export_to_txt(chat_id, filepath)

    @pyqtSlot()
    def on_export_zip_clicked(self):
        source_text = self.source_chat_input.text()
        if not source_text:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return
        match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not match: return
        chat_id = int(match.group(1))
        default_filename = f"chat_{chat_id}_export.zip"
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить ZIP-архив", default_filename, "ZIP Archives (*.zip);;All Files (*)")
        if filepath:
            self.telethon_client.start_export_to_zip(chat_id, filepath)

    @pyqtSlot()
    def on_forward_all_clicked(self):
        source_text = self.source_chat_input.text()
        dest_text = self.dest_chat_input.text()
        if not source_text or not dest_text:
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать исходный чат и указать ID целевого чата.")
            return
        source_match = re.search(r'\(ID: (-?\d+)\)', source_text)
        if not source_match: return
        try:
            source_chat_id = int(source_match.group(1))
            dest_chat_id = int(dest_text)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "ID целевого чата должен быть числом.")
            return
        self.telethon_client.start_forwarding_all(source_chat_id, dest_chat_id)

    @pyqtSlot(int)
    def on_forwarding_finished(self, count):
        QMessageBox.information(self, "Пересылка завершена", f"Всего было переслано {count} сообщений.")

    def closeEvent(self, event):
        self.log("Завершение работы...")
        if self.telethon_thread.isRunning():
            self.telethon_thread.quit()
            self.telethon_thread.wait()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
