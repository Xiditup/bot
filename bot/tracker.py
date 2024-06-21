from os import getenv
import httpx

def send_postback(subid: str):
    httpx.post(f"{getenv('POSTBACK_URL')}subid={subid}&status=lead")