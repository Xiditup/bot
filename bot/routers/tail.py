from aiogram import Router
from aiogram.types import Message

tail = Router()

@tail.message()
async def delete_message(msg: Message):
    await msg.delete()