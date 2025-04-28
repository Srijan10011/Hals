# session_manager.py
import os
import random
import asyncio
from telethon import TelegramClient, events
from config import SESSION_FOLDER, API_ID, API_HASH, TG_BOT_ID, OTP_FETCH_TIMEOUT
from send2trash import send2trash

async def pick_random_session():
    sessions = [f for f in os.listdir(SESSION_FOLDER) if f.endswith('.session')]
    if not sessions:
        return None, None
    chosen = random.choice(sessions)
    phone = chosen.replace('.session', '')
    return phone, os.path.join(SESSION_FOLDER, chosen)

async def delete_session_after_use(session_file):
    # Move the session file to the recycle bin after OTP is fetched
    send2trash(session_file)
    print(f"Session file {session_file} has been moved to the recycle bin.")


async def listen_for_code(session_file: str):
    """
    Connects with the given Telethon session, waits up to OTP_FETCH_TIMEOUT
    seconds for a new login code from TG_BOT_ID, then returns it.
    """
    client = TelegramClient(session_file.replace('.session', ''), API_ID, API_HASH)
    await client.start()
    code = None

    @client.on(events.NewMessage(from_users=TG_BOT_ID, incoming=True))
    async def handler(event):
        nonlocal code
        text = event.raw_text or ""
        # look for a 5–6 digit code
        match = __import__('re').search(r"\b(\d{5,6})\b", text)
        if match:
            code = match.group(1)
            await client.disconnect()

    try:
        # run until disconnected by handler, or timeout
        await asyncio.wait_for(client.run_until_disconnected(), timeout=OTP_FETCH_TIMEOUT)
    except asyncio.TimeoutError:
        await client.disconnect()

    return code
