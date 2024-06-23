from os import getenv
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n, SimpleI18nMiddleware
from aiogram.types import BotCommand, FSInputFile, Update

from fastapi import FastAPI, Request
import uvicorn

import routers

from storage import DatabaseProcessor

from middlewares import MyI18NMW

dbp = DatabaseProcessor()


logging.basicConfig()

bot = Bot(getenv('BOT_TOKEN'))
ADMIN_CHAT_ID = getenv('ADMIN_ID')
dp = Dispatcher()
#dp.update.outer_middleware(SimpleI18nMiddleware(I18n(path='locales', default_locale='en', domain='messages')))
dp.update.outer_middleware(
    MyI18NMW(
        I18n(
            path='locales',
            default_locale='en',
            domain='messages'
        )
    )
)

dp.include_router(routers.head)
dp.include_router(routers.info)
dp.include_router(routers.account)
dp.include_router(routers.birds)
dp.include_router(routers.withdrawal)
dp.include_router(routers.tail)
    
async def lifespan(app: FastAPI):
    for i in range(5):
        msg = await bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=FSInputFile(path=f'/app/static/{i}.jpg')
        )
        dbp.set_photoid(f'{i}', msg.photo[-1].file_id)

    for name in  ['account', 'birds', 'info', 'main', 'topup', 'withdrawal']:
        msg = await bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=FSInputFile(path=f'/app/static/{name}.jpg'),
        )
        dbp.set_photoid(f'{name}', msg.photo[-1].file_id)
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

'''
async def main():
    for i in range(5):
        msg = await bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=FSInputFile(path=f'/app/static/{i}.jpg')
        )
        dbp.set_photoid(f'{i}', msg.photo[-1].file_id)

    for name in  ['account', 'birds', 'info', 'main', 'topup', 'withdrawal']:
        msg = await bot.send_photo(
            chat_id=ADMIN_CHAT_ID,
            photo=FSInputFile(path=f'/app/static/{name}.jpg'),
        )
        dbp.set_photoid(f'{name}', msg.photo[-1].file_id)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    '''
if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port='80')
    #asyncio.run(main())