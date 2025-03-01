import pytest
from unittest.mock import AsyncMock, patch
from resume_bot.bot.handlers import start, receive_job_description, receive_files

@pytest.mark.asyncio
async def test_start():
    update = AsyncMock()
    context = AsyncMock()
    update.message.reply_text = AsyncMock()

    await start(update, context)

    update.message.reply_text.assert_called_once_with('Hello! Share the job title and its description.')

@pytest.mark.asyncio
async def test_receive_job_description():
    update = AsyncMock()
    context = AsyncMock()
    update.message.text = "Software Engineer at XYZ Corp"
    update.message.reply_text = AsyncMock()

    await receive_job_description(update, context)

    update.message.reply_text.assert_any_call('Loading...')
    update.message.reply_text.assert_any_call('Extracted Keywords:\n')
    update.message.reply_text.assert_any_call('Send your current resume in PDF format.')

@pytest.mark.asyncio
async def test_receive_files():
    update = AsyncMock()
    context = AsyncMock()
    update.message.document.file_id = "file_id"
    update.message.document.file_name = "resume.pdf"
    update.message.document = update.message.document
    update.effective_chat.id = 12345
    update.message.reply_text = AsyncMock()
    context.bot.get_file = AsyncMock(return_value=AsyncMock(download_as_bytearray=AsyncMock(return_value=b"content")))
    
    await receive_files(update, context)

    update.message.reply_text.assert_called_once_with('Received resume.pdf')