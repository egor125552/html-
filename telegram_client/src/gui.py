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
        self.setGeometry(100, 100, 1000, 700) # Increased window size
        self.all_chats = []
        self.init_ui()
        self.init_telethon_thread()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Левая панель (Исходные чаты) ---
        source_panel_layout = QVBoxLayout()
        source_list_label = QLabel("1. Выберите ИСХОДНЫЙ чат:")
        self.source_chat_list = QListWidget()
        self.source_chat_list.setAccessibleName("Список исходных чатов")
        self.source_chat_list.currentItemChanged.connect(self.on_source_chat_changed)
        source_panel_layout.addWidget(source_list_label)
        source_panel_layout.addWidget(self.source_chat_list)

        # --- Средняя панель (Целевые чаты) ---
        dest_panel_layout = QVBoxLayout()
        dest_list_label = QLabel("2. Выберите ЦЕЛЕВОЙ чат:")
        self.dest_chat_list = QListWidget()
        self.dest_chat_list.setAccessibleName("Список целевых чатов")
        self.dest_chat_list.currentItemChanged.connect(self.on_dest_chat_changed)
        dest_panel_layout.addWidget(dest_list_label)
        dest_panel_layout.addWidget(self.dest_chat_list)

        # --- Правая панель (Управление и Логи) ---
        right_panel_layout = QVBoxLayout()

        # Секция управления
        controls_layout = QVBoxLayout()
        source_chat_label = QLabel("Исходный чат:")
        self.source_chat_display = QLineEdit()
        self.source_chat_display.setReadOnly(True)
        dest_chat_label = QLabel("Целевой чат:")
        self.dest_chat_display = QLineEdit()
        self.dest_chat_display.setReadOnly(True)

        self.count_button = QPushButton("Подсчитать сообщения в исходном")
        self.count_button.clicked.connect(self.on_count_button_clicked)
        self.export_txt_button = QPushButton("Экспорт исходного в .txt")
        self.export_txt_button.clicked.connect(self.on_export_txt_clicked)
        self.export_zip_button = QPushButton("Экспорт исходного в .zip")
        self.export_zip_button.clicked.connect(self.on_export_zip_clicked)
        self.forward_all_button = QPushButton("Переслать ВСЕ из исходного в целевой")
        self.forward_all_button.clicked.connect(self.on_forward_all_clicked)

        controls_layout.addWidget(source_chat_label)
        controls_layout.addWidget(self.source_chat_display)
        controls_layout.addWidget(dest_chat_label)
        controls_layout.addWidget(self.dest_chat_display)
        controls_layout.addWidget(self.count_button)
        controls_layout.addWidget(self.export_txt_button)
        controls_layout.addWidget(self.export_zip_button)
        controls_layout.addWidget(self.forward_all_button)

        # Секция логов
        log_label = QLabel("Логи и статус:")
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)

        right_panel_layout.addLayout(controls_layout)
        right_panel_layout.addWidget(log_label)
        right_panel_layout.addWidget(self.log_widget)

        # Сборка основного макета
        main_layout.addLayout(source_panel_layout, 1)
        main_layout.addLayout(dest_panel_layout, 1)
        main_layout.addLayout(right_panel_layout, 2)

        self.setStatusBar(QStatusBar(self))
        self.log("Приложение запущено.")

    def init_telethon_thread(self):
        # ... (Эта функция остается без изменений)
        self.telethon_thread = QThread()
        self.telethon_client = TelethonClient()
        self.telethon_client.moveToThread(self.telethon_thread)
        self.telethon_client.dialogs_ready.connect(self.update_chat_lists)
        self.telethon_client.status_update.connect(self.log)
        self.telethon_client.message_count_ready.connect(self.on_message_count_ready)
        self.telethon_client.export_finished.connect(self.on_export_finished)
        self.telethon_client.forwarding_finished.connect(self.on_forwarding_finished)
        self.telethon_client.phone_required.connect(self.prompt_for_phone)
        self.telethon_client.code_required.connect(self.prompt_for_code)
        self.telethon_client.password_required.connect(self.prompt_for_password)
        self.telethon_thread.finished.connect(self.telethon_thread.deleteLater)
        self.telethon_thread.started.connect(self.telethon_client.start_connecting)
        self.telethon_thread.start()

    # --- Слоты для входа (остаются без изменений) ---
    @pyqtSlot()
    def prompt_for_phone(self):
        text, ok = QInputDialog.getText(self, 'Требуется номер телефона', 'Пожалуйста, введите ваш номер телефона:')
        if ok and text: self.telethon_client.send_phone(text)
    @pyqtSlot()
    def prompt_for_code(self):
        text, ok = QInputDialog.getText(self, 'Требуется код', 'Пожалуйста, введите код, полученный в Telegram:')
        if ok and text: self.telethon_client.send_code(text)
    @pyqtSlot()
    def prompt_for_password(self):
        text, ok = QInputDialog.getText(self, 'Требуется пароль', 'Пароль (2FA):', QLineEdit.EchoMode.Password)
        if ok and text: self.telethon_client.send_password(text)

    # --- Основные слоты ---
    @pyqtSlot(str)
    def log(self, message):
        self.log_widget.append(message)
        self.statusBar().showMessage(message)

    @pyqtSlot(list)
    def update_chat_lists(self, chats):
        self.log(f"Получено {len(chats)} чатов. Обновление списков...")
        self.all_chats = chats
        self.source_chat_list.clear()
        self.dest_chat_list.clear()
        for chat in chats:
            self.source_chat_list.addItem(chat['name'])
            self.dest_chat_list.addItem(chat['name'])
        self.log("Списки чатов обновлены.")

    def _get_chat_id_from_display(self, display_widget):
        text = display_widget.text()
        if not text: return None
        match = re.search(r'\(ID: (-?\d+)\)', text)
        return int(match.group(1)) if match else None

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_source_chat_changed(self, current, previous):
        if not current: return
        chat_data = next((chat for chat in self.all_chats if chat['name'] == current.text()), None)
        if chat_data:
            self.source_chat_display.setText(f"{chat_data['name']} (ID: {chat_data['id']})")

    @pyqtSlot(QListWidgetItem, QListWidgetItem)
    def on_dest_chat_changed(self, current, previous):
        if not current: return
        chat_data = next((chat for chat in self.all_chats if chat['name'] == current.text()), None)
        if chat_data:
            self.dest_chat_display.setText(f"{chat_data['name']} (ID: {chat_data['id']})")

    @pyqtSlot()
    def on_count_button_clicked(self):
        chat_id = self._get_chat_id_from_display(self.source_chat_display)
        if chat_id is None:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат из списка.")
            return
        self.telethon_client.start_message_count(chat_id)

    @pyqtSlot()
    def on_export_txt_clicked(self):
        chat_id = self._get_chat_id_from_display(self.source_chat_display)
        if chat_id is None:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат.")
            return
        default_filename = f"chat_{chat_id}_export.txt"
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить экспорт чата", default_filename, "Text Files (*.txt)")
        if filepath:
            self.telethon_client.start_export_to_txt(chat_id, filepath)

    @pyqtSlot()
    def on_export_zip_clicked(self):
        chat_id = self._get_chat_id_from_display(self.source_chat_display)
        if chat_id is None:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, сначала выберите исходный чат.")
            return
        default_filename = f"chat_{chat_id}_export.zip"
        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить ZIP-архив", default_filename, "ZIP Archives (*.zip)")
        if filepath:
            self.telethon_client.start_export_to_zip(chat_id, filepath)

    @pyqtSlot()
    def on_forward_all_clicked(self):
        source_chat_id = self._get_chat_id_from_display(self.source_chat_display)
        dest_chat_id = self._get_chat_id_from_display(self.dest_chat_display)
        if source_chat_id is None or dest_chat_id is None:
            QMessageBox.warning(self, "Ошибка", "Необходимо выбрать и исходный, и целевой чат.")
            return
        self.telethon_client.start_forwarding_all(source_chat_id, dest_chat_id)

    @pyqtSlot(int)
    def on_message_count_ready(self, count):
        QMessageBox.information(self, "Результат подсчета", f"Всего сообщений в исходном чате: {count}")

    @pyqtSlot(str)
    def on_export_finished(self, filepath):
        QMessageBox.information(self, "Экспорт завершен", f"История чата сохранена:\n{filepath}")

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
