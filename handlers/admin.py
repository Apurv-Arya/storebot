from aiogram import Router, types, F
from database.db import DB_PATH
from utils.config import ADMIN_IDS
import aiosqlite

router = Router()

def is_admin(uid): return uid in ADMIN_IDS

@router.message(F.text.startswith("/addcat"))
async def add_category(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    _, name = msg.text.split(" ", 1)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        await db.commit()
    await msg.answer(f"✅ Category '{name}' added.")

@router.message(F.text.startswith("/additem"))
async def add_item(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    try:
        _, title, price, stock, category, *desc = msg.text.split(" ", 5)
        desc = desc[0] if desc else ""
        price, stock = float(price), int(stock)
    except:
        return await msg.answer("⚠️ /additem <title> <price> <stock> <category> <desc?>")
    async with aiosqlite.connect(DB_PATH) as db:
        cat_cursor = await db.execute("SELECT category_id FROM categories WHERE name = ?", (category,))
        cat = await cat_cursor.fetchone()
        if not cat:
            return await msg.answer("❌ Category not found.")
        await db.execute("INSERT INTO items (title, price, stock, description, category_id) VALUES (?, ?, ?, ?, ?)",
                         (title, price, stock, desc, cat[0]))
        await db.commit()
    await msg.answer(f"✅ Item '{title}' added.")

@router.message(F.text.startswith("/upload"))
async def upload_content(msg: types.Message):
    if not is_admin(msg.from_user.id): return
    try:
        _, item_id = msg.text.split()
    except:
        return await msg.answer("⚠️ Usage: /upload <item_id> (reply to content)")
    if not msg.reply_to_message:
        return await msg.answer("📎 Reply to the message with content")
    content = msg.reply_to_message.text or msg.reply_to_message.document.file_id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (item_id, content) VALUES (?, ?)", (item_id, content))
        await db.commit()
    await msg.answer("✅ Content uploaded.")

@router.message(F.text.startswith("/setbalance"))
async def set_user_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")
    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = float(amount)
    except:
        return await message.answer("⚠️ Usage: /setbalance <user_id> <amount>")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, user_id))
        await db.commit()
    await message.answer(f"✅ User {user_id} balance set to ${amount:.2f}")

