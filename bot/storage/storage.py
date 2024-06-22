from string import ascii_uppercase
from redis import Redis
from misc.models import User, datetime, source_panel
from misc.exceptions import UserAlreadyExists
from tracker import send_postback

r = Redis(host='redis', port=6379)

class DatabaseProcessor:
    def __init__(self):
        self.r = r

    def _create_code(self, tg_id: int) -> str:
        return ''.join([ascii_uppercase[int(d)] for d in str(tg_id)])
    
    def _decrypt_code(self, code: str) -> int:
        return int(''.join([str(ascii_uppercase.index(c)) for c in code]))

    def _validate_code(self, code: str) -> bool:
        if code == None:
            return False
        if 'FACEBOOK-' in code:
            send_postback(code.split('-')[-1])
            return False
        try:
            ref_id = self._decrypt_code(code)
        except:
            return False
        return self._user_exists(ref_id)
    
    def _add_referral(self, ref_id: int, tg_id: int):
        u = self._get_user(ref_id)
        u.referrals_count += 1
        u.referrals.append(tg_id)
        self.update_user(u)

    def _create_user(self, tg_id: int, link_domain: str, code: str | None) -> User:
        referrer = None
        if self._validate_code(code):
            referrer = self._decrypt_code(code)
            self._add_referral(referrer, tg_id)
        
        return User(
            tg_id=tg_id,
            coin_balance=100,
            withdrawal_coin_balance=10,
            referrer=referrer,
            referrals_count=0,
            referrals=[],
            last_check=datetime.now(),
            source_amounts=[0,0,0,0,0],
            source_balances=[0,0,0,0,0],
            link=f'{link_domain}?start=a_{self._create_code(tg_id)}',
            payment_history=[],
            first_withdrawal=True,
            language_code='en'
        )
    
    def _user_exists(self, tg_id: int) -> bool:
        return bool(r.get(tg_id))

    def register_user(self, tg_id: int, link_domain: str, code: str | None) -> bool:
        if not self._user_exists(tg_id):
            u = self._create_user(tg_id, link_domain, code)
            r.set(tg_id, u.model_dump_json())
            return True
        return False

    def update_user(self, u: User) -> User:
        r.set(u.tg_id, u.model_dump_json())
        return u
    
    def _get_user(self, tg_id: int) -> User:
        return User.model_validate_json(r.get(tg_id))
    
    def get_brl(self, tg_id: int):
        u = self._get_user(tg_id)
        return [u.coin_balance, u.referrals_count, u.link]
    
    def get_eab(self, tg_id: int) -> list[list[int] | int]:
        u = self._get_user(tg_id)
        u.update()
        self.update_user(u)
        return [sum(u.source_balances), u.source_amounts, u.source_balances]
    
    def collect_eggs(self, tg_id: int):
        u = self._get_user(tg_id)
        u.update()
        u.coin_balance += sum(u.source_balances)
        u.source_balances = [0,0,0,0,0]
        self.update_user(u)

    def get_bird_amount(self, tg_id: int, bird_id: int) -> int:
        u = self._get_user(tg_id)
        return u.source_amounts[bird_id]
    
    def buy_bird(self, tg_id: int, bird_id: int) -> bool:
        u = self._get_user(tg_id)
        cost = source_panel[bird_id].cost
        if u.coin_balance >= cost:
            u.update()
            u.source_amounts[bird_id] += 1
            u.coin_balance -= cost
            self.update_user(u)
            return True
        return False
    
    def update_referrer(self, ref_id: int, amount: int):
        refal_stars_to_refer_wcoins = {
            50: 3,
            100: 6,
            500: 32,
            1000: 67
        }
        u = self._get_user(ref_id)
        u.withdrawal_coin_balance += refal_stars_to_refer_wcoins[amount]
        self.update_user(u)
    
    def register_payment(self, tg_id: int, charge_id: str, amount: int):
        u = self._get_user(tg_id)
        u.payment_history.append((amount, charge_id))
        stars_to_bucks = {
            50: 0.65,
            100: 1.30,
            500: 6.50,
            1000: 13.00
        }
        stars_to_silver = {
            50: 6500,
            100: 13000,
            500: 65000,
            1000: 130000
        }
        stars_to_withdrawal_points = {
            50: 26,
            100: 52,
            500: 260,
            1000: 540
        }
        u.coin_balance += stars_to_silver[amount]
        u.withdrawal_coin_balance += stars_to_withdrawal_points[amount]

        if u.referrer:
            self.update_referrer(u.referrer, amount)

        self.update_user(u)

    def first_withdrawal(self, tg_id: int) -> bool:
        u = self._get_user(tg_id)
        return u.first_withdrawal
    
    def get_silver(self, tg_id: int) -> int:
        u = self._get_user(tg_id)
        return u.coin_balance

    def validate_ton_address(self, addr: str) -> bool:
        #TODO: implement
        return False

    def fw_acuired(self, tg_id: int):
        u = self._get_user(tg_id)
        u.first_withdrawal = False
        u.withdrawal_coin_balance -= 10
        self.update_user(u)

    def get_silver_gold(self, tg_id: int) -> list[int]:
        u = self._get_user(tg_id)
        return [u.coin_balance, u.withdrawal_coin_balance]
    
    def get_gold(self, tg_id: int) -> int:
        u = self._get_user(tg_id)
        return u.withdrawal_coin_balance
    
    def set_photoid(self, key: str, photo_id: int):
        self.r.set(f'photos-{key}', photo_id)

    def get_photoid(self, key: str) -> int:
        return self.r.get(f'photos-{key}')
    
    def update_language_code(self, tg_id: int, language_code: str):
        u = self._get_user(tg_id)
        u.language_code = language_code
        self.update_user(u)

    def get_language_code(self, tg_id: int) -> str:
        try:
            u = self._get_user(tg_id)
            return u.language_code
        except:
            return