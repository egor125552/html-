import asyncio
import os
import zipfile
import tempfile
import shutil
from PyQt6.QtCore import QObject, pyqtSignal
from telethon import TelegramClient
from telethon.tl.types import MessageService

# --- Конфигурация ---
API_ID = 23883645
API_HASH = 'd14551e03adb7251eabff4dab1d9004d'
SESSION_NAME = 'anon'

class TelethonClient(QObject):
    dialogs_ready = pyqtSignal(list)
    status_update = pyqtSignal(str)
    message_count_ready = pyqtSignal(int)
    export_finished = pyqtSignal(str)
    forwarding_finished = pyqtSignal(int)
    phone_required = pyqtSignal()
    code_required = pyqtSignal()
    password_required = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH, system_version="4.16.30-vxCUSTOM")
        self.loop = asyncio.new_event_loop()
        self._phone_event = asyncio.Event()
        self._code_event = asyncio.Event()
        self._password_event = asyncio.Event()
        self._phone = ""
        self._code = ""
        self._password = ""

    def send_phone(self, phone):
        self._phone = phone
        self.loop.call_soon_threadsafe(self._phone_event.set)

    def send_code(self, code):
        self._code = code
        self.loop.call_soon_threadsafe(self._code_event.set)

    def send_password(self, password):
        self._password = password
        self.loop.call_soon_threadsafe(self._password_event.set)

    def start_connecting(self):
        asyncio.set_event_loop(self.loop)
        self.loop.create_task(self._connect_with_login())
        self.loop.run_forever()

    def start_message_count(self, chat_id):
        asyncio.run_coroutine_threadsafe(self._count_messages(chat_id), self.loop)

    def start_export_to_txt(self, chat_id, filepath):
        asyncio.run_coroutine_threadsafe(self._export_to_txt(chat_id, filepath), self.loop)

    def start_export_to_zip(self, chat_id, options):
        filepath = options.get("filepath", "export.zip")
        self.status_update.emit(f"Запрос на экспорт чата {chat_id} в ZIP-архив {filepath}...")
        asyncio.run_coroutine_threadsafe(self._export_to_zip(chat_id, options), self.loop)

    def start_forwarding_all(self, source_chat_id, dest_chat_id):
        asyncio.run_coroutine_threadsafe(self._forward_all_messages(source_chat_id, dest_chat_id), self.loop)

    async def _get_phone(self):
        self._phone_event.clear()
        self.phone_required.emit()
        await self._phone_event.wait()
        return self._phone

    async def _get_code(self):
        self._code_event.clear()
        self.code_required.emit()
        await self._code_event.wait()
        return self._code

    async def _get_password(self):
        self._password_event.clear()
        self.password_required.emit()
        await self._password_event.wait()
        return self._password

    async def _connect_with_login(self):
        try:
            await self.client.connect()
            if not await self.client.is_user_authorized():
                await self.client.send_code_request(await self._get_phone())
                await self.client.sign_in(self._phone, await self._get_code())
            try:
                if not await self.client.is_user_authorized():
                     await self.client.sign_in(password=await self._get_password())
            except Exception:
                 pass
            if await self.client.is_user_authorized():
                self.status_update.emit("Авторизация прошла успешно!")
                await self._connect_and_fetch_dialogs()
            else:
                self.status_update.emit("Не удалось авторизоваться.")
        except Exception as e:
            self.status_update.emit(f"Ошибка при подключении: {e}")

    async def _connect_and_fetch_dialogs(self):
        try:
            dialogs = await self.client.get_dialogs(limit=None)
            chat_list = [{'id': dialog.id, 'name': dialog.name} for dialog in dialogs]
            chat_list.sort(key=lambda x: x['name'])
            self.dialogs_ready.emit(chat_list)
        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [получение чатов]: {e}")

    async def _count_messages(self, chat_id):
        try:
            messages = await self.client.get_messages(chat_id, limit=0)
            self.message_count_ready.emit(messages.total)
        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [подсчет]: {e}")

    async def _export_to_txt(self, chat_id, filepath, is_sub_task=False):
        try:
            if not is_sub_task:
                total = (await self.client.get_messages(chat_id, limit=0)).total
                self.status_update.emit(f"Начинаю экспорт {total} сообщений в {filepath}...")
            count = 0
            with open(filepath, 'w', encoding='utf-8') as f:
                async for message in self.client.iter_messages(chat_id):
                    sender = f"{message.sender.first_name or ''} {message.sender.last_name or ''}".strip() if message.sender else "N/A"
                    f.write(f"[{message.date.strftime('%Y-%m-%d %H:%M:%S')}] {sender}: {message.text or ''}\n")
                    count += 1
            if not is_sub_task:
                self.export_finished.emit(filepath)
        except Exception as e:
            self.status_update.emit(f"Ошибка Telethon [экспорт в txt]: {e}")

    async def _export_to_zip(self, chat_id, options):
        zip_filepath = options.get("filepath")
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                total = (await self.client.get_messages(chat_id, limit=0)).total
                self.status_update.emit(f"Начинаю экспорт ~{total} сообщений в {zip_filepath}...")

                if options.get("text"):
                    await self._export_to_txt(chat_id, os.path.join(temp_dir, "messages.html"), is_sub_task=True)

                download_map = {
                    "photos": options.get("photos"), "videos": options.get("videos"),
                    "voice": options.get("voice"), "video_notes": options.get("video_notes"),
                    "audio": options.get("audio"), "files": options.get("files")
                }

                count = 0
                async for message in self.client.iter_messages(chat_id):
                    count += 1
                    if count % 100 == 0:
                        self.status_update.emit(f"Проверено {count}/{total} сообщений...")

                    media_map = {
                        "photos": message.photo, "videos": message.video,
                        "voice": message.voice, "video_notes": message.video_note,
                        "audio": message.audio, "files": message.document
                    }

                    for media_type, should_download in download_map.items():
                        if should_download and media_map.get(media_type):
                            os.makedirs(os.path.join(temp_dir, media_type), exist_ok=True)
                            await self.client.download_media(
                                message.media,
                                file=os.path.join(temp_dir, media_type, f"{message.id}_{media_map.get(media_type).attributes[-1].file_name if hasattr(media_map.get(media_type).attributes[-1], 'file_name') else ''}")
                            )

                self.status_update.emit("Архивация файлов...")
                shutil.make_archive(zip_filepath.replace('.zip', ''), 'zip', temp_dir)
                self.export_finished.emit(zip_filepath)
            except Exception as e:
                self.status_update.emit(f"Ошибка Telethon [экспорт в ZIP]: {e}")

    async def _forward_all_messages(self, source_chat_id, dest_chat_id):
        try:
            self.status_update.emit("Получение общего количества сообщений для пересылки...")
            total_messages = (await self.client.get_messages(source_chat_id, limit=0)).total
            self.status_update.emit(f"Начинаю пересылку ~{total_messages} сообщений из {source_chat_id} в {dest_chat_id}...")

            success_count = 0
            failed_count = 0
            skipped_count = 0

            async for message in self.client.iter_messages(source_chat_id, reverse=True):
                if isinstance(message, MessageService):
                    skipped_count += 1
                    continue

                try:
                    await self.client.forward_messages(dest_chat_id, message.id, source_chat_id)
                    success_count += 1
                    if success_count % 50 == 0:
                        processed_count = success_count + failed_count + skipped_count
                        self.status_update.emit(f"Обработано: {processed_count}/{total_messages}. Переслано: {success_count}. Пропущено: {skipped_count}. Ошибок: {failed_count}. Пауза...")
                        await asyncio.sleep(5)
                except Exception:
                    failed_count += 1

            final_message = (
                f"Пересылка завершена.\n"
                f"  - Успешно переслано: {success_count}\n"
                f"  - Не удалось переслать (ошибки): {failed_count}\n"
                f"  - Пропущено (служ. сообщения): {skipped_count}"
            )
            self.status_update.emit(final_message)
            self.forwarding_finished.emit(success_count)
        except Exception as e:
            self.status_update.emit(f"Критическая ошибка Telethon [пересылка]: {e}")
