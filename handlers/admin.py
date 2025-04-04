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

@router.message(F.text == "/stats")
async def sales_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admins only.")

    async with aiosqlite.connect(DB_PATH) as db:
        tx_cursor = await db.execute(
            "SELECT COUNT(*), SUM(amount) FROM transactions WHERE type = 'purchase' AND status = 'success'"
        )
        tx_count, total_revenue = await tx_cursor.fetchone()

        cat_cursor = await db.execute("""
            SELECT c.name, COUNT(i.inventory_id)
            FROM inventory i
            JOIN items it ON i.item_id = it.item_id
            JOIN categories c ON it.category_id = c.category_id
            WHERE i.sold = 1
            GROUP BY c.category_id
        """)
        cat_sales = await cat_cursor.fetchall()

    total_revenue = total_revenue or 0.0
    msg = f"📊 <b>Sales Stats</b>\n\n"
    msg += f"🧾 Total Orders: <b>{tx_count}</b>\n"
    msg += f"💰 Total Revenue: <b>${total_revenue:.2f}</b>\n\n"

    if cat_sales:
        msg += "📦 <b>Items Sold by Category:</b>\n"
        for name, count in cat_sales:
            msg += f"• {name}: {count} sold\n"
    else:
        msg += "⚠️ No items sold yet."

    await message.answer(msg)

@router.message(F.text.startswith("/userstats"))
async def user_stats(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admins only.")

    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
    except:
        return await message.answer("⚠️ Usage: /userstats <user_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT COUNT(*), SUM(amount)
            FROM transactions
            WHERE user_id = ? AND type = 'purchase' AND status = 'success'
        """, (user_id,))
        count, total = await cursor.fetchone()
        total = total or 0.0

        item_cursor = await db.execute("""
            SELECT COUNT(*)
            FROM inventory
            WHERE sold_to = ?
        """, (user_id,))
        items = (await item_cursor.fetchone())[0]

    await message.answer(
        f"📊 <b>User Stats for {user_id}</b>\n\n"
        f"🧾 Purchases: <b>{count}</b>\n"
        f"📦 Items Received: <b>{items}</b>\n"
        f"💰 Total Spent: <b>${total:.2f}</b>"
    )

@router.message(F.text.startswith("/txhistory"))
async def transaction_history(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admins only.")

    try:
        _, user_id = message.text.split()
        user_id = int(user_id)
    except:
        return await message.answer("⚠️ Usage: /txhistory <user_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT tx_id, amount, type, status, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user_id,))
        txs = await cursor.fetchall()

    if not txs:
        return await message.answer("📭 No transactions found.")

    msg = f"🧾 <b>Last 10 Transactions for {user_id}</b>:\n\n"
    for tx in txs:
        msg += (
            f"• <b>ID:</b> {tx[0]} | <b>${tx[1]:.2f}</b>\n"
            f"   <b>Type:</b> {tx[2]} | <b>Status:</b> {tx[3]}\n"
            f"   🕒 {tx[4]}\n\n"
        )
    await message.answer(msg)
