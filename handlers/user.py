from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from database.db import DB_PATH
from keyboards.inline import main_menu_kb, category_menu_kb, orders_back_kb
import aiosqlite, datetime
from utils.config import STOREBOT_NAME, ADMIN_IDS

router = Router()

@router.message(F.text == "/start")
async def start_command(message: Message):
    user = message.from_user
    user_id = user.id
    username = user.username or "N/A"

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO users (user_id, username, balance, registered_at) VALUES (?, ?, ?, datetime('now'))",
                (user_id, username, 0.0)
            )
            balance = 0.0
        else:
            balance = row[0]

        await db.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        await db.commit()

    msg = (
        f"Hey There <b>@{username}!</b> 👋 Welcome to <b>{STOREBOT_NAME}</b>\n"
        f"💰 <b>Your Balance:</b> ${balance:.2f}\n\n"
        "Select an option below to get started 👇"
    )

    await message.answer(msg, parse_mode="HTML", reply_markup=main_menu_kb())

@router.callback_query(F.data == "browse_store")
async def browse_store(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT category_id, name FROM categories")
        cats = await cur.fetchall()
    if not cats:
        return await callback.message.edit_text("🚫 No categories available.")
    await callback.message.edit_text("📂 Choose a category:", reply_markup=category_menu_kb(cats))

@router.callback_query(F.data.startswith("cat_"))
async def list_items(callback: CallbackQuery):
    parts = callback.data.split("_")
    cat_id = int(parts[1])
    page = int(parts[2]) if len(parts) > 2 else 0
    per_page = 10
    offset = page * per_page

    async with aiosqlite.connect(DB_PATH) as db:
        # ✅ Safely fetch category name
        cursor = await db.execute("SELECT name FROM categories WHERE category_id = ?", (cat_id,))
        cat = await cursor.fetchone()
        category_name = cat[0] if cat else "Unknown"

        # ✅ Fetch items for this category
        cursor = await db.execute("""
            SELECT item_id, title, price, stock
            FROM items
            WHERE category_id = ? AND stock > 0
            LIMIT ? OFFSET ?
        """, (cat_id, per_page, offset))
        items = await cursor.fetchall()

        # ✅ Total count for pagination
        cursor = await db.execute("SELECT COUNT(*) FROM items WHERE category_id = ? AND stock > 0", (cat_id,))
        total = (await cursor.fetchone())[0]

    # Build inline keyboard
    kb = [[
        InlineKeyboardButton(text=f"{i[1]} - ${i[2]} ({i[3]})", callback_data=f"buy_{i[0]}")
    ] for i in items]

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"cat_{cat_id}_{page-1}"))
    if offset + per_page < total:
        nav.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"cat_{cat_id}_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton(text="⬅️ Back to Categories", callback_data="browse_store")])

    await callback.message.edit_text(
        f"📦 <b>{category_name}</b> (Page {page + 1})",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("buy_"))
async def buy_item(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT title, price FROM items WHERE item_id = ?", (item_id,))
        item = await cursor.fetchone()
        if not item:
            return await callback.answer("❌ Item not found.")
        title, price = item
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        balance = (await cursor.fetchone())[0]
        if balance < price:
            return await callback.answer("❌ Not enough balance.")
        cursor = await db.execute("SELECT inventory_id, content FROM inventory WHERE item_id = ? AND sold = 0 LIMIT 1", (item_id,))
        inv = await cursor.fetchone()
        if not inv:
            return await callback.answer("❌ Out of stock.")
        inventory_id, content = inv
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
        await db.execute("UPDATE inventory SET sold = 1, sold_to = ? WHERE inventory_id = ?", (user_id, inventory_id))
        # Update item stock
        await db.execute("UPDATE items SET stock = stock - 1 WHERE item_id = ?", (item_id,))
        await db.execute("INSERT INTO transactions (user_id, amount, type, status, created_at) VALUES (?, ?, ?, ?, ?)",
                         (user_id, price, "purchase", "success", datetime.datetime.now().isoformat()))

        # Check new stock level
        cursor = await db.execute("SELECT stock FROM items WHERE item_id = ?", (item_id,))
        new_stock = (await cursor.fetchone())[0]

        # Alert if low stock
        if new_stock <= 2:
             alert_text = (
                 f"⚠️ <b>Low Stock Alert</b>\n\n"
                 f"📦 Item: <b>{title}</b>\n"
                 f"📉 Remaining stock: <b>{new_stock}</b>\n"
                 f"🛒 Please restock soon!"
             )
             for admin_id in ADMIN_IDS:
                 try:
                     await callback.bot.send_message(admin_id, alert_text, parse_mode="HTML")
                 except Exception as e:
                     print(f"❌ Failed to alert admin {admin_id}: {e}")
        await db.commit()
    await callback.message.answer(f"✅ Here’s your product:\n\n{content}")

@router.message(F.text == "/info")
async def user_info(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "❌ No username"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        balance = row[0] if row else 0.0

    await message.answer(
        f"👤 <b>Your Info</b>\n\n"
        f"🆔 Telegram ID: <code>{user_id}</code>\n"
        f"🔗 Username: @{username}\n"
        f"💰 Balance: <b>${balance:.2f}</b>",
        parse_mode="HTML"
    )

@router.message(F.text == "/myorders")
async def my_orders(message: types.Message):
    user_id = message.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT i.inventory_id, it.title, i.content
            FROM inventory i
            JOIN items it ON it.item_id = i.item_id
            WHERE i.sold = 1 AND i.sold_to = ?
            ORDER BY i.inventory_id DESC
            LIMIT 10
        """, (user_id,))
        orders = await cursor.fetchall()

    if not orders:
        return await message.answer("📭 You haven’t purchased any items yet.")

    text = "📦 <b>Your Last 10 Orders</b>:\n\n"
    for idx, (inventory_id, title, content) in enumerate(orders, start=1):
        text += f"<b>{idx}.</b> {title}\n🧾 <code>{content[:50]}{'...' if len(content) > 50 else ''}</code>\n\n"

    await message.answer(text, parse_mode="HTML", reply_markup=orders_back_kb())

@router.message(F.text.startswith("/resend"))
async def resend_item(message: types.Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)

    if len(args) < 2:
        return await message.answer("⚠️ Usage: /resend <item title>")

    query = args[1].lower()

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT it.title, i.content
            FROM inventory i
            JOIN items it ON it.item_id = i.item_id
            WHERE i.sold_to = ? AND LOWER(it.title) LIKE ?
            ORDER BY i.inventory_id DESC
            LIMIT 1
        """, (user_id, f"%{query}%"))
        result = await cursor.fetchone()

    if not result:
        return await message.answer("❌ No matching item found in your purchase history.")

    title, content = result
    await message.answer(f"📦 <b>{title}</b> (Resent)\n\n<code>{content}</code>", parse_mode="HTML")

@router.callback_query(F.data == "menu_info")
async def menu_info(callback: CallbackQuery):
    user = callback.from_user
    user_id = user.id
    username = user.username or "N/A"

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        balance = row[0] if row else 0.0

    text = (
        f"👤 <b>Your Info</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🔗 Username: @{username}\n"
        f"💰 Balance: <b>${balance:.2f}</b>"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=main_menu_kb())

@router.callback_query(F.data == "menu_orders")
async def menu_orders(callback: CallbackQuery):
    user_id = callback.from_user.id

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT i.inventory_id, it.title, i.content
            FROM inventory i
            JOIN items it ON it.item_id = i.item_id
            WHERE i.sold = 1 AND i.sold_to = ?
            ORDER BY i.inventory_id DESC
            LIMIT 10
        """, (user_id,))
        orders = await cursor.fetchall()

    if not orders:
        return await callback.message.edit_text("📭 You haven’t purchased any items yet.")

    text = "📦 <b>Your Last 10 Orders</b>:\n\n"
    for idx, (inventory_id, title, content) in enumerate(orders, start=1):
        text += f"<b>{idx}.</b> {title}\n🧾 <code>{content[:50]}{'...' if len(content) > 50 else ''}</code>\n\n"

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=orders_back_kb())



