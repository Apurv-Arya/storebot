from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from database.db import DB_PATH
from keyboards.inline import main_menu_kb, category_menu_kb
import aiosqlite, datetime

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await db.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
        if not await user.fetchone():
            await db.execute("INSERT INTO users (user_id, registered_at) VALUES (?, ?)", (
                message.from_user.id, datetime.datetime.now().isoformat()))
            await db.commit()
    await message.answer("👋 Welcome to StoreBot! Choose an option:", reply_markup=main_menu_kb())

@router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT balance FROM users WHERE user_id = ?", (callback.from_user.id,))
        bal = (await cur.fetchone())[0]
    await callback.message.edit_text(f"💼 Your balance: ${bal:.2f}", reply_markup=main_menu_kb())

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
    per_page = 5
    offset = page * per_page

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT name FROM categories WHERE category_id = ?", (cat_id,))
        cat = await cursor.fetchone()
        cursor = await db.execute("SELECT item_id, title, price, stock FROM items WHERE category_id = ? AND stock > 0 LIMIT ? OFFSET ?",
                                  (cat_id, per_page, offset))
        items = await cursor.fetchall()
        cursor = await db.execute("SELECT COUNT(*) FROM items WHERE category_id = ? AND stock > 0", (cat_id,))
        total = (await cursor.fetchone())[0]

    kb = [[InlineKeyboardButton(f"{i[1]} - ${i[2]}", callback_data=f"buy_{i[0]}")] for i in items]
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"cat_{cat_id}_{page-1}"))
    if offset + per_page < total:
        nav.append(InlineKeyboardButton("➡️ Next", callback_data=f"cat_{cat_id}_{page+1}"))
    if nav:
        kb.append(nav)
    kb.append([InlineKeyboardButton("⬅️ Categories", callback_data="browse_store")])
    await callback.message.edit_text(f"📦 {cat[0]} Products (Page {page+1})", reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))

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
        await db.execute("UPDATE items SET stock = stock - 1 WHERE item_id = ?", (item_id,))
        await db.execute("INSERT INTO transactions (user_id, amount, type, status, created_at) VALUES (?, ?, ?, ?, ?)",
                         (user_id, price, "purchase", "success", datetime.datetime.now().isoformat()))
        await db.commit()
    await callback.message.answer(f"✅ Here’s your product:\n\n{content}")
