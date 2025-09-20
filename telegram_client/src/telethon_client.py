import asyncio
import os
import zipfile
from PyQt6.QtCore import QObject, pyqtSignal
from telethon import TelegramClient

# --- Конфигурация ---
# Берем из main.py, чтобы было в одном месте, но для клиента они нужны здесь
API_ID = 23883645
API_HASH = 'd14551e03adb7251eabff4dab1d9004d'
SESSION_NAME = 'anon'

class TelethonClient(QObject):
    """
    Класс для работы с Telethon в отдельном потоке.
    """
    # --- Сигналы для связи с GUI ---
    dialogs_ready = pyqtSignal(list)
    status_update = pyqtSignal(str)
    message_count_ready = pyqtSignal(int)
    export_finished = pyqtSignal(str) # filepath
    forwarding_finished = pyqtSignal(int) # count

    def __init__(self):
        super().__init__()
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH, system_version="4.16.30-vxCUSTOM")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    # --- Публичные методы (вызываются из GUI) ---

    def start_connecting(self):
        """Запускает процесс подключения и получения диалогов."""
        self.status_update.emit("Запуск асинхронного цикла...")
        self.loop.run_until_complete(self._connect_and_fetch_dialogs())

    def start_message_count(self, chat_id):
        """Запускает задачу подсчета сообщений в фоновом режиме."""
        self.status_update.emit(f"Запрос на подсчет сообщений для чата {chat_id}...")
        asyncio.run_coroutine_threadsafe(self._count_messages(chat_id), self.loop)

    def start_export_to_txt(self, chat_id, filepath):
        """Запускает задачу экспорта чата в .txt файл."""
        self.status_update.emit(f"Запрос на экспорт чата {chat_id} в файл {filepath}...")
        asyncio.run_coroutine_threadsafe(self._export_to_txt(chat_id, filepath), self.loop)

    def start_export_to_zip(self, chat_id, filepath):
        """Запускает задачу экспорта чата в .zip архив."""
        self.status_update.emit(f"Запрос на экспорт чата {chat_id} в ZIP-архив {filepath}...")
        asyncio.run_coroutine_threadsafe(self._export_to_zip(chat_id, filepath), self.loop)

    def start_forwarding_all(self, source_chat_id, dest_chat_id):
        """Запускает пересылку всех сообщений."""
        self.status_update.emit(f"Запрос на пересылку из {source_chat_id} в {dest_chat_id}...")
        asyncio.run_coroutine_threadsafe(self._forward_all_messages(source_chat_id, dest_chat_id), self.loop)

    # --- Приватные асинхронные методы (выполняются в цикле asyncio) ---

    async def _connect_and_fetch_dialogs(self):
        """Подключается к Telegram и загружает список диалогов."""
        try:
            if not self.client.is_connected():
                self.status_update.emit("Подключение к Telegram...")
                await self.client.connect()

            if not await self.client.is_user_authorized():
                self.status_update.emit("Ошибка: Сессия не авторизована.")
                return

            self.status_update.emit("Получение списка чатов...")
            dialogs = await self.client.get_dialogs(limit=None)

            chat_list = [{'id': dialog.id, 'name': dialog.name} for dialog in dialogs]
            chat_list.sort(key=lambda x: x['name'])

            self.dialogs_ready.emit(chat_list)
            self.status_update.emit("Список чатов успешно загружен.")

        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [подключение]: {e}")

    async def _count_messages(self, chat_id):
        """Подсчитывает сообщения в указанном чате."""
        try:
            self.status_update.emit(f"Подсчет сообщений в чате {chat_id}...")
            # client.get_messages с limit=0 не загружает сообщения, а только метаданные
            messages = await self.client.get_messages(chat_id, limit=0)
            count = messages.total
            self.status_update.emit(f"Найдено сообщений: {count}")
            self.message_count_ready.emit(count)
        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [подсчет]: {e}")

    async def _export_to_txt(self, chat_id, filepath):
        """Экспортирует все сообщения из чата в текстовый файл."""
        try:
            self.status_update.emit(f"Начинаю экспорт чата {chat_id} в {filepath}...")
            count = 0
            with open(filepath, 'w', encoding='utf-8') as f:
                # iter_messages - эффективный способ перебора всех сообщений
                async for message in self.client.iter_messages(chat_id):
                    sender = "N/A"
                    if message.sender:
                        sender = f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip()

                    text = message.text or "[Медиафайл или нет текстового содержимого]"

                    f.write(f"[{message.date.strftime('%Y-%m-%d %H:%M:%S')}] {sender}: {text}\n")
                    count += 1
                    if count % 100 == 0:
                        self.status_update.emit(f"Экспортировано {count} сообщений...")

            self.status_update.emit(f"Экспорт завершен. Всего экспортировано {count} сообщений в файл {filepath}.")
            self.export_finished.emit(filepath)

        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [экспорт]: {e}")

    async def _export_to_zip(self, chat_id, zip_filepath):
        """Экспортирует чат в .txt, а затем упаковывает в .zip."""
        try:
            # Создаем временный файл для экспорта
            temp_txt_filepath = zip_filepath.replace('.zip', '.txt')
            self.status_update.emit(f"Шаг 1/3: Экспорт во временный файл {temp_txt_filepath}...")

            # Используем уже существующую логику экспорта в .txt
            await self._export_to_txt(chat_id, temp_txt_filepath)

            self.status_update.emit(f"Шаг 2/3: Создание ZIP-архива {zip_filepath}...")
            with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.write(temp_txt_filepath, os.path.basename(temp_txt_filepath))

            self.status_update.emit(f"Шаг 3/3: Удаление временного файла...")
            os.remove(temp_txt_filepath)

            self.status_update.emit(f"ZIP-архив успешно создан: {zip_filepath}")
            self.export_finished.emit(zip_filepath)

        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [экспорт в ZIP]: {e}")

    async def _forward_all_messages(self, source_chat_id, dest_chat_id):
        """Пересылает все сообщения из одного чата в другой."""
        try:
            self.status_update.emit(f"Начинаю пересылку из {source_chat_id} в {dest_chat_id}...")
            count = 0
            # reverse=True важен для пересылки в хронологическом порядке (от старых к новым)
            async for message in self.client.iter_messages(source_chat_id, reverse=True):
                try:
                    await self.client.forward_messages(dest_chat_id, message.id, source_chat_id)
                    count += 1
                    if count % 50 == 0:
                        self.status_update.emit(f"Переслано {count} сообщений... делаю паузу во избежание флуда.")
                        await asyncio.sleep(5) # Пауза для избежания лимитов Telegram
                except Exception as e:
                    # Логируем ошибку для конкретного сообщения, но продолжаем
                    self.status_update.emit(f"Не удалось переслать сообщение {message.id}: {e}")
                    await asyncio.sleep(1) # Короткая пауза после ошибки

            self.status_update.emit(f"Пересылка завершена. Всего переслано {count} сообщений.")
            self.forwarding_finished.emit(count)

        except Exception as e:
            self.status_update.emit(f"Критическая ошибка Telethon [пересылка]: {e}")
        # finally:
            # Не отключаемся, чтобы клиент оставался активным для других операций
            # if self.client.is_connected():
            #     await self.client.disconnect()
            #     self.status_update.emit("Клиент отключен.")
