from os import getenv
import asyncio
import logging

from fastapi import FastAPI, Request
import uvicorn

from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware, ConstI18nMiddleware
from aiogram.types import Update, BotCommand, FSInputFile

import routers

from storage import DatabaseProcessor

dbp = DatabaseProcessor()


logging.basicConfig()

bot = Bot(getenv('BOT_TOKEN'))
help_bot = Bot(getenv('WD_BOT_TOKEN'))
ADMIN_CHAT_ID = getenv('ADMIN_ID')
dp = Dispatcher()
dp.update.outer_middleware(SimpleI18nMiddleware(I18n(path='locales', default_locale='en', domain='messages')))

dp.include_router(routers.head)
dp.include_router(routers.info)
dp.include_router(routers.account)
dp.include_router(routers.birds)
dp.include_router(routers.withdrawal)
dp.include_router(routers.tail)

async def lifespan(app: FastAPI):
    '''
    await bot.set_my_commands(commands=[
        BotCommand(command='/menu', description='Get main menu')
        ],
        language_code='en')
    
    await bot.set_my_commands(commands=[
        BotCommand(command='/menu', description='Λήψη κύριου μενού')
        ],
        language_code='lr_GR')
    
    await bot.set_my_commands(commands=[
        BotCommand(command='/menu', description='Pobierz menu główne')
        ],
        language_code='pl_PL')
        '''
    
    for i in range(5):
        msg = await help_bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=FSInputFile(path=f'/app/static/{i}.jpg')
        )
        dbp.set_photoid(f'{i}', msg.message_id)

    for name in  ['account', 'birds', 'info', 'main', 'topup', 'withdrawal']:
        msg = await help_bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=FSInputFile(path=f'/app/static/{name}.jpg')
        )
        dbp.set_photoid(f'{name}', msg.message_id)
    
    
    
    
    await bot.set_webhook(
        url=f"{getenv('WEBHOOK_URL')}/webhook",
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True
    )
    yield

app = FastAPI(lifespan=lifespan)

@app.post('/webhook')
async def recieve_tg_update(request: Request):
    update = Update.model_validate(await request.json(), context={"bot": bot})
    return await dp.feed_update(bot, update)

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port='80')