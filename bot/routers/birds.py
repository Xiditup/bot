from aiogram import Router, F
from aiogram.types import CallbackQuery, InputMediaPhoto, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.i18n import gettext as _
from storage import DatabaseProcessor
from misc.models import source_panel

birds = Router()

dbp = DatabaseProcessor()

async def menu(cbq: CallbackQuery):
    eggs, amounts, balances = dbp.get_eab(cbq.from_user.id)
    await cbq.message.edit_media(media=InputMediaPhoto(media=FSInputFile(path='/app/static/birds.jpg'),
                                                       caption=_('birds menu {eggs}').format(eggs=eggs)),
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text=_('bird 1 {amount} {balance}').format(
                                        amount=amounts[0],
                                        balance=balances[0]
                                    ), callback_data='bird-0')],
                                    [InlineKeyboardButton(text=_('bird 2 {amount} {balance}').format(
                                        amount=amounts[1],
                                        balance=balances[1]
                                    ), callback_data='bird-1')],
                                    [InlineKeyboardButton(text=_('bird 3 {amount} {balance}').format(
                                        amount=amounts[2],
                                        balance=balances[2]
                                    ), callback_data='bird-2')],
                                    [InlineKeyboardButton(text=_('bird 4 {amount} {balance}').format(
                                        amount=amounts[3],
                                        balance=balances[3]
                                    ), callback_data='bird-3')],
                                    [InlineKeyboardButton(text=_('bird 5 {amount} {balance}').format(
                                        amount=amounts[4],
                                        balance=balances[4]
                                    ), callback_data='bird-4')],
                                    [InlineKeyboardButton(text=_('collect'), callback_data='collect')],
                                    [InlineKeyboardButton(text=_('btn back to main'), callback_data='main')]
                                ]))

@birds.callback_query(F.data == 'birds')
async def birds_menu(cbq: CallbackQuery):
    await menu(cbq)
    
@birds.callback_query(F.data == 'collect')
async def collect(cbq: CallbackQuery):
    dbp.collect_eggs(cbq.from_user.id)
    await cbq.answer(text=_('eggs collected'))
    await menu(cbq)

async def bird(cbq: CallbackQuery, id: int):
    amount = dbp.get_bird_amount(cbq.from_user.id, id)
    text = [
        _('bird 1 {amount}').format(amount=amount),
        _('bird 2 {amount}').format(amount=amount),
        _('bird 3 {amount}').format(amount=amount),
        _('bird 4 {amount}').format(amount=amount),
        _('bird 5 {amount}').format(amount=amount)
    ][id]
    await cbq.message.edit_media(InputMediaPhoto(media=FSInputFile(path=f'/app/static/{id}.jpg'),
                                                 caption=text),
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text=_('buy'), callback_data=f'buy-{id}')],
                                    [InlineKeyboardButton(text=_('btn back to birds'), callback_data='birds')]
                                ]))

@birds.callback_query(F.data.startswith('bird'))
async def bird_menu(cbq: CallbackQuery):
    id = int(cbq.data.split('-')[-1])
    await bird(cbq, id)
    
@birds.callback_query(F.data.startswith('buy'))
async def buy(cbq: CallbackQuery):
    id = int(cbq.data.split('-')[-1])
    if dbp.buy_bird(cbq.from_user.id, id):
        await cbq.answer(text=_('Buy success'))
        await bird(cbq, id)
    else:
        await cbq.answer(text=_('Insufficient balance'),
                         show_alert=True)