from os import getenv
import logging
from aiogram import Bot, Router, F, html
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReactionTypeEmoji, FSInputFile, InputMediaPhoto, CallbackQuery, SwitchInlineQueryChosenChat
from aiogram.utils.i18n import gettext as _
from storage import DatabaseProcessor

logging.basicConfig()

head = Router()

bot = Bot(getenv('BOT_TOKEN'))

dbp = DatabaseProcessor()

async def menu(msg: Message | CallbackQuery, welcome=False):
    if isinstance(msg, CallbackQuery):
        msg = msg.message
    markup = InlineKeyboardMarkup(inline_keyboard=[
                               [InlineKeyboardButton(text=_('btn info'), callback_data='info')],
                               [InlineKeyboardButton(text=_('btn birds'), callback_data='birds')],
                               [InlineKeyboardButton(text=_('btn account'), callback_data='account')],
                               [InlineKeyboardButton(text=_('btn withdrawal'), callback_data='withdrawal')],
                               [InlineKeyboardButton(text=_('btn support'), url=getenv('SUPPORT_CONTACT'))]
                           ])
    if welcome:
        await msg.answer(text='Choose your language:\n\nWybierz swój język:\n\nΕπιλέξτε τη γλώσσα σας:',
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                             [InlineKeyboardButton(text='English language', callback_data='setlang-en')],
                             [InlineKeyboardButton(text='Język polski', callback_data='setlang-pl_PL')],
                             [InlineKeyboardButton(text='Ελληνική γλώσσα', callback_data='setlang-el_GR')]
                         ]))
        #await msg.answer_photo(photo=dbp.get_photoid('main'),
                            #caption=_('welcome {name}').format(name=msg.from_user.full_name),
                            #reply_markup=markup
                            #)
    else:
        try:
            await msg.edit_media(media=InputMediaPhoto(media=dbp.get_photoid('main'),
                                                    caption=_('main menu')),
                                reply_markup=markup)
        except:
            await msg.answer_photo(photo=dbp.get_photoid('main'),
                                caption=_('main menu'),
                                reply_markup=markup
                            )
            
@head.callback_query(F.data.startswith('setlang-'))
async def setlang(cbq: CallbackQuery):
    language_code = cbq.data.split('-')[-1]
    dbp.update_language_code(cbq.from_user.id, language_code)
    await cbq.message.delete()
    await menu(cbq)

@head.message(CommandStart())
async def start(msg: Message):
    code = None
    if 'a_' in msg.text:
        code = msg.text.split('_')[-1]
    if dbp.register_user(msg.from_user.id, getenv('LINK_DOMAIN'), code):
        await menu(msg, welcome=True)
    else:
        await msg.delete()

@head.message(Command('menu'))
async def get_main_menu(msg: Message):
    await menu(msg)
    await bot.delete_messages(msg.chat.id,
                              message_ids=[
                                  msg.message_id,
                                  msg.message_id - 1,
                                  msg.message_id - 2
                              ])


@head.callback_query(F.data == 'main')
async def main_menu(cbq: CallbackQuery):
    await menu(cbq)