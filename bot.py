# bot.py
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import db
import session_manager
import config
import shutil
import os

def move_to_sold(file_path):
    sold_folder = os.path.join(os.path.dirname(file_path), "sold")
    os.makedirs(sold_folder, exist_ok=True)
    shutil.move(file_path, os.path.join(sold_folder, os.path.basename(file_path)))

bot = Bot(token=config.BOT_TOKEN)
dp  = Dispatcher()

# ─── Bot Handlers ───────────────────────────────────────────────────────────────

@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    db.add_user(msg.from_user.id, msg.from_user.username)
    await msg.reply(
        "👋 Welcome!\n"
        "• /balance — Check your credits\n"
        "• /getnumber — Reserve a number\n"
        "• /getcode — Fetch OTP for your reserved number"
    )

@dp.message(Command("balance"))
async def cmd_balance(msg: types.Message):
    credits = db.get_credits(msg.from_user.id)
    await msg.reply(f"💰 You have {credits} credit(s).")

@dp.message(Command("addcredit"))
async def cmd_addcredit(msg: types.Message):
    if msg.from_user.id not in config.ADMIN_IDS:
        return
    parts = msg.text.split()
    if len(parts) != 3:
        return await msg.reply("Usage: /addcredit @username amount")
    username = parts[1].lstrip('@')
    try:
        amount = int(parts[2])
    except ValueError:
        return await msg.reply("Amount must be an integer.")
    cur = db.conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE username = ?', (username,))
    row = cur.fetchone()
    if not row:
        return await msg.reply("User not found in database.")
    db.add_credit(row[0], amount)
    await msg.reply(f"✅ Added {amount} credit(s) to @{username}.")

@dp.message(Command("getnumber"))
async def cmd_getnumber(msg: types.Message):
    user_id = msg.from_user.id
    # free expired before new reservation
    db.free_expired_reservations(config.RESERVATION_TIMEOUT)

    if db.get_reserved_number(user_id):
        pn, *_ = db.get_reserved_number(user_id)
        return await msg.reply(f"🔒 You already have reserved: {pn}")

    phone, session_file = await session_manager.pick_random_session()
    if not phone:
        return await msg.reply("❌ No numbers available right now. Please try later.")

    if db.is_number_reserved(phone):
        return await msg.reply("⚠️ Conflict detected, please try again.")

    db.reserve_number(user_id, phone, session_file)
    await msg.reply(f"✅ Your reserved number is: `{phone}`\nSend /getcode to fetch OTP.", parse_mode="Markdown")


# Cancel Reserved Number Command Handler
@dp.message(Command("cancel"))
async def cancel(message: types.Message):
    # Check if the user has a reserved number
    reserved_number = db.get_reserved_number(message.from_user.id)

    if not reserved_number:
        await message.reply("You don't have any number reserved to cancel.")
        return

    # Release the reserved number from the database
    db.release_number(message.from_user.id)

    await message.reply("Your reserved number has been successfully canceled.")


@dp.message(Command("getcode"))
async def cmd_getcode(msg: types.Message):
    user_id = msg.from_user.id
    # clean up expired
    db.free_expired_reservations(config.RESERVATION_TIMEOUT)

    res = db.get_reserved_number(user_id)
    if not res:
        return await msg.reply("❌ No reserved number. Use /getnumber first.")
    phone, session_file, _ = res

    if db.get_credits(user_id) <= 0:
        return await msg.reply("⚠️ You have no credits left. Ask admin to add more.")

    await msg.reply(f"⏳ Fetching OTP for `{phone}`...", parse_mode="Markdown")
    try:
        code = await session_manager.listen_for_code(session_file)
    except Exception as e:
        return await msg.reply(f"❌ Error while fetching OTP: {e}")

    if not code:
        return await msg.reply("⚠️ No OTP received. Try again later.")

    # success!
    await msg.reply(f"🔑 Your OTP for `{phone}` is: `{code}`", parse_mode="Markdown")

    # deduct credit & release number
    db.remove_credit(user_id, 1)
    db.release_number(user_id)

    remaining = db.get_credits(user_id)
    await msg.reply(f"✅ 1 credit deducted. You now have {remaining} credit(s).")
    # Delete the session file after OTP is fetched
    await session_manager.delete_session_after_use(session_file)

# ─── Main ──────────────────────────────────────────────────────────────────────

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
