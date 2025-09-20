import asyncio
import unittest
import tempfile
import datetime
import zipfile
from unittest.mock import MagicMock, AsyncMock, patch
from telethon.tl.types import User, Message

# Add the src directory to the path to allow imports
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from telethon_client import TelethonClient

class TestTelethonClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        """Set up a new TelethonClient for each test."""
        # We patch the TelegramClient during the instantiation of our class
        with patch('telethon.TelegramClient', new_callable=MagicMock) as MockTelethonClient:
            # The client inside TelethonClient will be a mock
            self.telethon_client_instance = TelethonClient()
            self.mock_tg_client = self.telethon_client_instance.client

            # Mock the signals to check if they are called
            self.telethon_client_instance.status_update = MagicMock()
            self.telethon_client_instance.message_count_ready = MagicMock()
            self.telethon_client_instance.export_finished = MagicMock()
            self.telethon_client_instance.forwarding_finished = MagicMock()

    async def test_count_messages(self):
        """Tests the message counting logic."""
        # Arrange: Configure the mock client's behavior
        chat_id = -100123456
        expected_count = 42

        # The result of get_messages should be an object with a 'total' attribute
        mock_messages_result = MagicMock()
        mock_messages_result.total = expected_count
        self.mock_tg_client.get_messages = AsyncMock(return_value=mock_messages_result)

        # Act: Call the method we want to test
        await self.telethon_client_instance._count_messages(chat_id)

        # Assert: Check if the correct signal was emitted with the correct value
        self.telethon_client_instance.message_count_ready.emit.assert_called_once_with(expected_count)

        # Check that status updates were emitted
        self.assertTrue(self.telethon_client_instance.status_update.emit.called)

    async def test_export_to_txt(self):
        """Tests the chat export to .txt functionality."""
        # Arrange
        chat_id = -100123456

        # Create a mock sender object
        mock_sender = MagicMock()
        mock_sender.first_name = "Test"
        mock_sender.last_name = "User"

        # Create mock message objects using MagicMock for robustness
        msg1 = MagicMock()
        msg1.date = datetime.datetime.now(datetime.timezone.utc)
        msg1.text = "Hello"
        msg1.sender = mock_sender

        msg2 = MagicMock()
        msg2.date = datetime.datetime.now(datetime.timezone.utc)
        msg2.text = "World"
        msg2.sender = mock_sender

        mock_messages = [msg1, msg2]

        # Configure the mock client's async generator
        async def mock_iter_messages(*args, **kwargs):
            for msg in mock_messages:
                yield msg

        self.mock_tg_client.iter_messages = mock_iter_messages

        # Also need to mock get_messages for the total count
        mock_total = MagicMock()
        mock_total.total = len(mock_messages)
        self.mock_tg_client.get_messages = AsyncMock(return_value=mock_total)

        # Act
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8') as tmp:
            filepath = tmp.name
            await self.telethon_client_instance._export_to_txt(chat_id, filepath)

            # Assert inside the with block, before file is closed/deleted
            tmp.seek(0)
            content = tmp.read()
            self.assertIn("Hello", content)
            self.assertIn("World", content)
            self.assertIn("Test User", content)

        # Assert that the finished signal was called with the correct filepath
        self.telethon_client_instance.export_finished.emit.assert_called_once_with(filepath)

    @patch('zipfile.ZipFile')
    @patch('os.remove')
    async def test_export_to_zip(self, mock_os_remove, mock_zipfile):
        """Tests the ZIP export functionality by mocking the file operations."""
        # Arrange
        chat_id = -100123456
        zip_filepath = "/tmp/test.zip"

        # We can mock the internal _export_to_txt call since it's already tested
        self.telethon_client_instance._export_to_txt = AsyncMock()

        # Act
        await self.telethon_client_instance._export_to_zip(chat_id, zip_filepath)

        # Assert
        # 1. Check that the internal .txt export was called
        self.telethon_client_instance._export_to_txt.assert_called_once()

        # 2. Check that a ZipFile was created
        mock_zipfile.assert_called_once_with(zip_filepath, 'w', zipfile.ZIP_DEFLATED)

        # 3. Check that the temporary file was removed
        mock_os_remove.assert_called_once()

        # 4. Check that the final signal was emitted
        self.telethon_client_instance.export_finished.emit.assert_called_once_with(zip_filepath)

    async def test_forward_all_messages(self):
        """Tests the message forwarding logic."""
        # Arrange
        source_chat_id = -100123
        dest_chat_id = -100456

        # Create mock message objects
        mock_messages = [MagicMock(id=i) for i in range(5)] # 5 mock messages

        async def mock_iter_messages(*args, **kwargs):
            for msg in mock_messages:
                yield msg

        self.mock_tg_client.iter_messages = mock_iter_messages
        self.mock_tg_client.forward_messages = AsyncMock()

        # Mock the get_messages call for the total count
        mock_total = MagicMock()
        mock_total.total = len(mock_messages)
        self.mock_tg_client.get_messages = AsyncMock(return_value=mock_total)

        # Act
        await self.telethon_client_instance._forward_all_messages(source_chat_id, dest_chat_id)

        # Assert
        # 1. Check that forward_messages was called for each message
        self.assertEqual(self.mock_tg_client.forward_messages.call_count, len(mock_messages))

        # 2. Check that the final signal was emitted with the correct count
        self.telethon_client_instance.forwarding_finished.emit.assert_called_once_with(len(mock_messages))

if __name__ == '__main__':
    unittest.main()
