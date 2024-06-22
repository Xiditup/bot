import logging

from aiogram import Router
from aiogram.types import Message

logging.basicConfig()

tail = Router()

@tail.message()
async def delete_message(msg: Message):
    await msg.delete()