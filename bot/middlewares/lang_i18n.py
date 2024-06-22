from typing import Any, Dict
from aiogram.types import TelegramObject, User
from aiogram.utils.i18n import I18n, I18nMiddleware, SimpleI18nMiddleware
from typing import Optional

from storage import DatabaseProcessor

dbp = DatabaseProcessor()

class MyI18NMW(I18nMiddleware):
    async def get_locale(self, event: TelegramObject, data: Dict[str, Any]) -> str:
        event_from_user: Optional[User] = data.get("event_from_user", None)
        if event_from_user:
            return dbp.get_language_code(event_from_user.id) or self.i18n.default_locale
        else:
            return self.i18n.default_locale