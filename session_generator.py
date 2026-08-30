from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
import asyncio


async def generate_string_session(api_id, api_hash, phone_number):
    """
    Generate string session dari nomor HP + OTP.
    Client dikembalikan dalam keadaan connected, siap dipakai buat complete_login().
    """
    string_session = StringSession()
    client = TelegramClient(string_session, api_id, api_hash)

    await client.connect()
    await client.send_code_request(phone_number)

    return client, string_session


async def complete_login(client, phone_number, code, password=None):
    """
    Selesaikan login dengan OTP (dan password 2FA kalau perlu).
    Raise SessionPasswordNeededError kalau akun butuh password dan belum dikasih,
    supaya caller (bot.py) bisa minta password lalu panggil ulang fungsi ini.
    """
    try:
        if password is not None:
            await client.sign_in(password=password)
        else:
            await client.sign_in(phone=phone_number, code=code)
    except SessionPasswordNeededError:
        if password is None:
            raise  # caller harus minta password dan panggil ulang
        raise

    string_session = client.session.save()
    await client.disconnect()
    return string_session
