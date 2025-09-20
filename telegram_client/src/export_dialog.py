import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox,
    QLabel, QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog
)

class ExportDialog(QDialog):
    """
    Диалоговое окно для настройки параметров экспорта.
    """
    def __init__(self, parent=None, default_filename="export.zip"):
        super().__init__(parent)
        self.setWindowTitle("Настройки экспорта в ZIP")

        layout = QVBoxLayout(self)

        # --- Выбор типа контента ---
        content_label = QLabel("Выберите, что вы хотите экспортировать:")
        layout.addWidget(content_label)

        self.cb_text = QCheckBox("История сообщений (.txt)")
        self.cb_text.setChecked(True)
        layout.addWidget(self.cb_text)

        self.cb_photos = QCheckBox("Фотографии")
        self.cb_photos.setChecked(True)
        layout.addWidget(self.cb_photos)

        self.cb_videos = QCheckBox("Видео")
        self.cb_videos.setChecked(True)
        layout.addWidget(self.cb_videos)

        self.cb_voice = QCheckBox("Голосовые сообщения")
        self.cb_voice.setChecked(True)
        layout.addWidget(self.cb_voice)

        self.cb_video_notes = QCheckBox("Видеосообщения (кружки)")
        self.cb_video_notes.setChecked(True)
        layout.addWidget(self.cb_video_notes)

        self.cb_audio = QCheckBox("Аудиофайлы / Музыка")
        self.cb_audio.setChecked(True)
        layout.addWidget(self.cb_audio)

        self.cb_files = QCheckBox("Другие файлы / Документы")
        self.cb_files.setChecked(True)
        layout.addWidget(self.cb_files)

        # --- Выбор пути сохранения ---
        path_label = QLabel("Путь для сохранения архива:")
        layout.addWidget(path_label)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(default_filename)
        self.browse_button = QPushButton("Обзор...")
        self.browse_button.clicked.connect(self.browse_for_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        layout.addLayout(path_layout)

        # --- Кнопки OK и Cancel ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def browse_for_path(self):
        """Открывает диалог выбора пути для сохранения файла."""
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить ZIP-архив",
            self.path_edit.text(),
            "ZIP Archives (*.zip)"
        )
        if filepath:
            self.path_edit.setText(filepath)

    def get_options(self):
        """Возвращает словарь с выбранными параметрами."""
        return {
            "text": self.cb_text.isChecked(),
            "photos": self.cb_photos.isChecked(),
            "videos": self.cb_videos.isChecked(),
            "voice": self.cb_voice.isChecked(),
            "video_notes": self.cb_video_notes.isChecked(),
            "audio": self.cb_audio.isChecked(),
            "files": self.cb_files.isChecked(),
            "filepath": self.path_edit.text()
        }

# Пример запуска для тестирования
if __name__ == '__main__':
    app = QApplication(sys.argv)
    dialog = ExportDialog()
    if dialog.exec():
        print("Выбранные опции:", dialog.get_options())
    else:
        print("Экспорт отменен.")
    sys.exit(0)
