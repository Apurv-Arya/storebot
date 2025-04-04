from aiogram import Router, types, F
from database.models import DB_PATH
from utils.config import ADMIN_IDS
import aiosqlite

router = Router()

def is_admin(uid): return uid in ADMIN_IDS

@router.message(F.text.startswith("/addcat"))
async def add_category(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")
    try:
        _, name = message.text.split(" ", 1)
    except:
        return await message.answer("⚠️ Usage: /addcat <Category Name>")
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            await db.commit()
            await message.answer(f"✅ Category '{name}' added.")
        except:
            await message.answer("⚠️ Category exists.")

@router.message(F.text.startswith("/additem"))
async def add_item(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")
    try:
        _, title, price, stock, category, *desc = message.text.split(" ", 5)
        price, stock = float(price), int(stock)
        desc = desc[0] if desc else ""
    except:
        return await message.answer("⚠️ Usage: /additem <title> <price> <stock> <category> <desc?>")
    async with aiosqlite.connect(DB_PATH) as db:
        cat_cursor = await db.execute("SELECT category_id FROM categories WHERE name = ?", (category,))
        cat = await cat_cursor.fetchone()
        if not cat:
            return await message.answer("❌ Category not found.")
        cat_id = cat[0]
        await db.execute("INSERT INTO items (title, price, stock, description, category_id) VALUES (?, ?, ?, ?, ?)",
                         (title, price, stock, desc, cat_id))
        await db.commit()
        await message.answer(f"✅ Item '{title}' added.")

@router.message(F.text.startswith("/upload"))
async def upload_content(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")
    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /upload <item_id> (reply with content)")
    if not message.reply_to_message:
        return await message.answer("📎 Reply to a message with the content")
    content = message.reply_to_message.text or message.reply_to_message.document.file_id
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO inventory (item_id, content) VALUES (?, ?)", (item_id, content))
        await db.commit()
    await message.answer("📦 Uploaded.")

@router.message(F.text.startswith("/setbalance"))
async def set_balance(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")
    try:
        _, uid, amount = message.text.split()
        uid = int(uid)
        amount = float(amount)
    except:
        return await message.answer("⚠️ Usage: /setbalance <user_id> <amount>")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET balance = ? WHERE user_id = ?", (amount, uid))
        await db.commit()
    await message.answer(f"✅ Balance set: {uid} → ${amount:.2f}")

@router.message(F.text == "/catstats")
async def category_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT c.name, COUNT(i.inventory_id) 
            FROM inventory i
            JOIN items it ON it.item_id = i.item_id
            JOIN categories c ON it.category_id = c.category_id
            WHERE i.sold = 1
            GROUP BY c.category_id
        """)
        rows = await cursor.fetchall()
    if not rows:
        return await message.answer("📊 No stats.")
    text = "📊 Category Stats:\n\n"
    for name, count in rows:
        text += f"• {name}: {count} sold\n"
    await message.answer(text)
