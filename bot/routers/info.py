import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from storage import DatabaseProcessor

dbp = DatabaseProcessor()

logging.basicConfig()

info = Router()

@info.callback_query(F.data == 'info')
async def info_menu(cbq: CallbackQuery):
    await cbq.message.edit_media(
        media=InputMediaPhoto(media=dbp.get_photoid('info'),
                              caption=_('info')),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('btn back to main'), callback_data='main')]
        ])
    )