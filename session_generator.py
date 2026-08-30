from telethon import TelegramClient
from telethon.sessions import StringSession
import asyncio

async def generate_string_session(api_id, api_hash, phone_number):
    """
    Generate string session dari nomor HP + OTP
    """
    string_session = StringSession()
    client = TelegramClient(string_session, api_id, api_hash)
    
    await client.connect()
    
    # Kirim kode OTP
    await client.send_code_request(phone_number)
    
    # Tunggu user input OTP (akan dihandle di bot)
    # Return client untuk step selanjutnya
    return client, string_session

async def complete_login(client, phone_number, code, password=None):
    """
    Selesaikan login dengan OTP
    """
    try:
        await client.sign_in(phone=phone_number, code=code)
    except Exception as e:
        if "password" in str(e).lower():
            # 2FA enabled
            await client.sign_in(phone=phone_number, password=password)
    
    # Get string session
    string_session = client.session.save()
    await client.disconnect()
    
    return string_session