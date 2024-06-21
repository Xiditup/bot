from datetime import datetime
from pydantic import BaseModel

class Source(BaseModel):
    cost: int
    production: int

source_panel = [
    Source(
        cost=100,
        production=10,
    ),
    Source(
        cost=300,
        production=50,
    ),
    Source(
        cost=1000,
        production=100,
    ),
    Source(
        cost=3000,
        production=200,
    ),
    Source(
        cost=10000,
        production=500,
    )
]

class User(BaseModel):
    tg_id: int
    coin_balance: int
    withdrawal_coin_balance: int
    referrer: int | None
    referrals_count: int
    referrals: list[int]
    last_check: datetime
    source_amounts: list[int]
    source_balances: list[int]
    link: str
    payment_history: list[tuple]
    first_withdrawal: bool

    def update(self):
        now = datetime.now()
        for i in range(5):
            self.source_balances[i] += int((now - self.last_check).seconds * source_panel[i].production * self.source_amounts[i] / 3600)
        self.last_check = now