from os import getenv
import logging
from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery, ReplyParameters
from aiogram.utils.i18n import gettext as _
from storage import DatabaseProcessor

logging.basicConfig()

bot = Bot(token=getenv('BOT_TOKEN'))
account = Router()

dbp = DatabaseProcessor()

async def menu(cbq: CallbackQuery | Message):
    balance, referrals, link = dbp.get_brl(cbq.from_user.id)
    keyboard = [
            [InlineKeyboardButton(text=_('share my link'), switch_inline_query_current_chat=_('share this: {link}').format(
                link=link
            ))],
            [InlineKeyboardButton(text=_('top up balance'), callback_data='topup')],
            [InlineKeyboardButton(text=_('btn back to main'), callback_data='main')]
        ]
    file = FSInputFile(path='/app/static/account.jpg')
    text = _('account {balance} {referrals}').format(
                balance=balance,
                referrals=referrals
                )
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    if isinstance(cbq, CallbackQuery):
        await cbq.message.edit_media(media=InputMediaPhoto(media=file, caption=text),
                                    reply_markup=markup)
    else:
        await cbq.answer_photo(photo=file, caption=text, reply_markup=markup)
    
@account.callback_query(F.data == 'account')
async def account_menu(cbq: CallbackQuery):
    await menu(cbq)

@account.callback_query(F.data == 'topup')
async def topup(cbq: CallbackQuery):
    await cbq.message.edit_media(InputMediaPhoto(media=FSInputFile(path='/app/static/topup.jpg'),
                                                 caption=_('topup info')),
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text=_('pay 50'), callback_data='pay-50')],
                                    [InlineKeyboardButton(text=_('pay 100'), callback_data='pay-100')],
                                    [InlineKeyboardButton(text=_('pay 500'), callback_data='pay-500')],
                                    [InlineKeyboardButton(text=_('pay 1000'), callback_data='pay-1000')],
                                    [InlineKeyboardButton(text=_('back to account'), callback_data='account')]
                                ]))
    
@account.callback_query(F.data.startswith('pay'))
async def pay(cbq: CallbackQuery):
    invoice_titles = {
        50: _('invoice 50 title'),
        100: _('invoice 100 title'),
        500: _('invoice 500 title'),
        1000: _('invoice 1000 title'),
    }
    amount = int(cbq.data.split('-')[-1])
    await cbq.message.answer_invoice(
        title=invoice_titles[amount],
        description=_('invoice description'),
        prices=[
            LabeledPrice(label='XTR', amount=amount)
        ],
        provider_token='',
        payload='deposit',
        currency='XTR',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=_('send payment'), pay=True)],
            [InlineKeyboardButton(text=_('cancel invoice'), callback_data='delete-invoice')]
        ])
    )

@account.callback_query(F.data == 'delete-invoice')
async def delete_invoice(cbq: CallbackQuery):
    await cbq.message.delete()

@account.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pcq.id, True)

@account.message(F.successful_payment)
async def payment_handler(msg: Message):
    dbp.register_payment(msg.from_user.id,
                         msg.successful_payment.telegram_payment_charge_id,
                         msg.successful_payment.total_amount)
    await bot.delete_messages(chat_id=msg.from_user.id,
                              message_ids=[
                                  msg.message_id - 1,
                                  msg.message_id - 2
                              ])
    await menu(msg)