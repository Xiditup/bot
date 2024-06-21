from os import getenv
import asyncio
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.types import StarTransactions, StarTransaction, TransactionPartnerUser, User
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from storage import DatabaseProcessor

bot = Bot(token=getenv('BOT_TOKEN'))
withdrawal_operator_bot = Bot(token=getenv('WD_BOT_TOKEN'))

withdrawal = Router()

class WContext(StatesGroup):
    AskTONaddr = State()

dbp = DatabaseProcessor()
        
async def first_menu(cbq: CallbackQuery, answer=False):
    silver = dbp.get_silver(cbq.from_user.id)
    keyboard = [
            [InlineKeyboardButton(text=_('to fw 0.1$'), callback_data='to-fw')],
            [InlineKeyboardButton(text=_('to main menu'), callback_data='main')]
        ]
    if answer:
        await cbq.message.answer_photo(photo=FSInputFile(path='/app/static/withdrawal.jpg'),
                                 caption=_('fw menu {silver}').format(silver=silver),
                                 reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await cbq.message.edit_media(media=InputMediaPhoto(media=FSInputFile(path='/app/static/withdrawal.jpg'),
                                                        caption=_('fw menu {silver}').format(silver=silver)),
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

async def menu(cbq: CallbackQuery | Message):
    silver = dbp.get_silver(cbq.from_user.id)
    keyboard = [
                [InlineKeyboardButton(text=_('to wd'), callback_data='to-wd')],
                [InlineKeyboardButton(text=_('to main menu'), callback_data='main')]
        ]
    if isinstance(cbq, CallbackQuery):
        await cbq.message.edit_media(media=InputMediaPhoto(media=FSInputFile(path='/app/static/withdrawal.jpg'),
                                                        caption=_('wd menu {silver}').format(silver=silver)),
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await cbq.answer_photo(photo=FSInputFile(path='/app/static/withdrawal.jpg'),
                               caption=_('wd menu {silver}').format(silver=silver),
                               reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@withdrawal.callback_query(F.data == 'withdrawal')
async def withdrawal_menu(cbq: CallbackQuery):
    if dbp.first_withdrawal(cbq.from_user.id):
        await first_menu(cbq)
    else:
        await menu(cbq)

@withdrawal.callback_query(F.data == 'to-fw')
async def fwd(cbq: CallbackQuery):
    silver = dbp.get_silver(cbq.from_user.id)
    if silver >= 1000:
        await cbq.message.edit_caption(caption=_('fw available {silver}').format(silver=silver),
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                           [InlineKeyboardButton(text=_('request fw'), callback_data=('request-fw'))],
                                           [InlineKeyboardButton(text=_('to wd menu'), callback_data='withdrawal')]
                                       ]))
    else:
        await cbq.message.edit_caption(caption=_('not available fw {silver}').format(silver=silver),
                                       reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                           [InlineKeyboardButton(text=_('to wd menu'), callback_data='withdrawal')]
                                       ]))
    
@withdrawal.callback_query(F.data == 'request-fw')
async def fw_request(cbq: CallbackQuery, state: FSMContext):
    await cbq.message.delete()
    await cbq.message.answer(text=_('ask TON addr (WARNING: YOU MUST ENTER CORRECT DATA. IF MISTAKE OCCURED, CONTACT SUPPORT IMMEDIATELY!!!)'),
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text=_('cancel fw'), callback_data='cancel-fw')]
                             ]))
    await state.set_state(WContext.AskTONaddr)

@withdrawal.callback_query(WContext.AskTONaddr, F.data == 'cancel-fw')
async def cancel_fw(cbq: CallbackQuery, state: FSMContext):
    await state.clear()
    await cbq.message.delete()
    await first_menu(cbq, answer=True)

@withdrawal.message(WContext.AskTONaddr)
async def proceed_fw(msg: Message, state: FSMContext):
    await withdrawal_operator_bot.send_message(
        chat_id=getenv('ADMIN_ID'),
        text=f'First withdrawal request from:\nTG_ID: {msg.from_user.id}\nTON ADDRESS: {msg.text}'
    )
    await bot.delete_messages(msg.from_user.id, message_ids=[
        msg.message_id, msg.message_id - 1
    ])
    await state.clear()
    dbp.fw_acuired(msg.from_user.id)
    await msg.answer(text=_('fw money will arrive in next 24h.'))
    await menu(msg)

async def wd_menu(cbq: CallbackQuery | Message, answer=False):
    silver, gold = dbp.get_silver_gold(cbq.from_user.id)
    available = 0.01 * gold
    keyboard = [
                [InlineKeyboardButton(text=_('request'), callback_data='request-wd')],
                [InlineKeyboardButton(text=_('gold'), callback_data='to-gold')],
                [InlineKeyboardButton(text=_('wd to menu'), callback_data='withdrawal')]
            ]
    text = _('wd menu {silver} {gold} {available}').format(
                                                            silver=silver,
                                                            gold=gold,
                                                            available=available
                                                        )
    if isinstance(cbq, CallbackQuery):
        if not answer:
            await cbq.message.edit_caption(caption=text,
                                            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
                                )
        else:
            await cbq.message.answer_photo(photo=FSInputFile(path='/app/static/withdrawal.jpg'),
                                           caption=text,
                                           reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        if answer:
            await cbq.answer_photo(photo=FSInputFile(path='/app/static/withdrawal.jpg'),
                                           caption=text,
                                           reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))

@withdrawal.callback_query(F.data == 'to-wd')
async def wd_handler(cbq: CallbackQuery):
    await wd_menu(cbq)

@withdrawal.callback_query(F.data == 'to-gold')
async def gold_menu(cbq: CallbackQuery):
    gold = dbp.get_gold(cbq.from_user.id)
    await cbq.message.edit_caption(caption=_('gold menu promt {gold}').format(gold=gold),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text=_('gold details'), callback_data='to-gold-details')],
                                       [InlineKeyboardButton(text=_('to tasks'), callback_data='tasks')],
                                       [InlineKeyboardButton(text=_('back from gold menu to wd menu'), callback_data='to-wd')]
                                   ]))
    
@withdrawal.callback_query(F.data == 'to-gold-details')
async def gold_details(cbq: CallbackQuery):
    await cbq.message.edit_caption(caption=_('gold details promt, table, etc.'),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [InlineKeyboardButton(text=_('back from gold details to gold menu'), callback_data='to-gold')]
                                   ]))
    
@withdrawal.callback_query(F.data == 'tasks')
async def tasks_menu(cbq: CallbackQuery):
    #TODO: IMPLELENT!
    await cbq.answer(text=_('Currently there are NO tasks :('),
                     show_alert=True)

class MainWDContext(StatesGroup):
    AskSum = State()
    AskTONaddr = State()

@withdrawal.callback_query(F.data == 'request-wd')
async def request_wd(cbq: CallbackQuery, state: FSMContext):
    silver, gold = dbp.get_silver_gold(cbq.from_user.id)
    available = 0.01 * gold
    await cbq.message.answer(text=_('ask amount to wd. available: {available}').format(available=available),
                             reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                 [InlineKeyboardButton(text=_('cancel wd'), callback_data='cancel-wd')]
                             ]))
    await state.set_state(MainWDContext.AskSum)
    await cbq.message.delete()

@withdrawal.callback_query(MainWDContext.AskSum, F.data == 'cancel-wd')
async def cancel_wd_on_sum(cbq: CallbackQuery, state: FSMContext):
    await state.clear()
    msg = cbq.message
    await bot.delete_messages(chat_id=msg.from_user.id,
                              message_ids=[msg.message_id,
                                           msg.message_id - 1,
                                           msg.message_id - 2,
                                           msg.message_id - 3,
                                           msg.message_id - 4])
    await wd_menu(cbq, answer=True)

@withdrawal.callback_query(MainWDContext.AskTONaddr, F.data == 'cancel-wd')
async def cancel_wd_on_addr(cbq: CallbackQuery, state: FSMContext):
    await state.clear()
    msg = cbq.message
    await bot.delete_messages(chat_id=msg.from_user.id,
                              message_ids=[msg.message_id,
                                           msg.message_id + 1,
                                           msg.message_id - 1,
                                           msg.message_id - 2,
                                           msg.message_id - 3,
                                           msg.message_id - 4])
    await wd_menu(cbq, answer=True)

@withdrawal.message(MainWDContext.AskSum)
async def set_sum(msg: Message, state: FSMContext):
    await state.update_data(summ=msg.text)
    await msg.answer(text=_('ask ton addr to wd'))
    await state.set_state(MainWDContext.AskTONaddr)

@withdrawal.message(MainWDContext.AskTONaddr)
async def proceed_wd(msg: Message, state: FSMContext):
    data = await state.get_data()
    summ = data['summ']
    addr = msg.text
    available = dbp.get_gold(msg.from_user.id) * 0.01
    await withdrawal_operator_bot.send_message(chat_id=getenv('ADMIN_ID'),
                                               text=f'Withdrawal request:\nTG_ID: {msg.from_user.id}\nAmount: {summ}\nAvailable: {available}\nTON address: {addr}')
    await bot.delete_messages(chat_id=msg.from_user.id,
                              message_ids=[msg.message_id,
                                           msg.message_id - 1,
                                           msg.message_id - 2,
                                           msg.message_id - 3,
                                           msg.message_id - 4])
    await msg.answer(text=_('Withdrawal request sucess promt (manager, support, 24h, etc)'))
    await state.clear()
    await wd_menu(msg, answer=True)