from aiogram import Router, F, types
from database.models import DB_PATH
from utils.config import ADMIN_IDS
import aiosqlite

router = Router()

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(F.text.startswith("/additem"))
async def add_item(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Access denied.")
    
    try:
        _, title, price, stock, *desc = message.text.split(" ", 4)
        price, stock = float(price), int(stock)
        desc = desc[0] if desc else ""
    except:
        return await message.answer("⚠️ Usage: /additem <title> <price> <stock> <description?>")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO items (title, price, stock, description) VALUES (?, ?, ?, ?)",
                         (title, price, stock, desc))
        await db.commit()

    await message.answer("✅ Item added.")

@router.message(F.text.startswith("/upload"))
async def upload_content(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Access denied.")

    parts = message.text.strip().split(" ", 1)
    if len(parts) != 2:
        return await message.answer("⚠️ Usage: /upload <item_id> followed by content")
    
    item_id = int(parts[1])
    if not message.reply_to_message:
        return await message.answer("📎 Reply to a message containing the content to upload.")

    content = message.reply_to_message.text or message.reply_to_message.document.file_id

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (item_id, content) VALUES (?, ?)", (item_id, content))
        await db.commit()

    await message.answer("📦 Content uploaded successfully.")

@router.message(F.text.startswith("/setbalance"))
async def set_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Access denied.")
    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = float(amount)
    except:
        return await message.answer("⚠️ Usage: /setbalance <user_id> <amount>")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, uid))
        await db.commit()

    await message.answer(f"✅ Balance set for user {uid} to ${amount:.2f}")

@router.message(F.text.startswith("/stats"))
async def view_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Access denied.")

    async with aiosqlite.connect(DB_PATH) as db:
        txs = await db.execute("SELECT COUNT(*), SUM(amount) FROM transactions WHERE type = 'purchase'")
        count, total = await txs.fetchone()
    await message.answer(f"📊 Total Sales: {count} orders\n💸 Revenue: ${total:.2f if total else 0.00}")
