from aiogram import Router, types, F
from aiogram.types import Message, CallbackQuery
from database.models import DB_PATH
import aiosqlite
from keyboards.inline import main_menu_kb, store_item_kb
import datetime

router = Router()

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        user = await db.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
        if not await user.fetchone():
            await db.execute("INSERT INTO users (user_id, registered_at) VALUES (?, ?)", (
                message.from_user.id, datetime.datetime.now().isoformat()))
            await db.commit()
    await message.answer("👋 Welcome to the Store Bot! Choose an option:", reply_markup=main_menu_kb())

@router.callback_query(F.data == "check_balance")
async def check_balance(callback: CallbackQuery):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (callback.from_user.id,))
        bal = await cursor.fetchone()
        balance = bal[0] if bal else 0
    await callback.message.edit_text(f"💼 Your balance: ${balance:.2f}", reply_markup=main_menu_kb())

@router.callback_query(F.data == "browse_store")
async def browse_store(callback: CallbackQuery):
    text = "🛒 Available items:\n\n"
    kb = []
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT item_id, title, price, stock FROM items WHERE stock > 0") as cursor:
            rows = await cursor.fetchall()
            for item in rows:
                text += f"🔹 {item[1]} — ${item[2]} [{item[3]} in stock]\n"
                kb.append([types.InlineKeyboardButton(
                    text=f"Buy {item[1]}",
                    callback_data=f"buy_{item[0]}"
                )])
    markup = types.InlineKeyboardMarkup(inline_keyboard=kb + [[
        types.InlineKeyboardButton("⬅️ Back", callback_data="main_menu")
    ]])
    await callback.message.edit_text(text, reply_markup=markup)

@router.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: CallbackQuery):
    item_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    async with aiosqlite.connect(DB_PATH) as db:
        # Get item
        cursor = await db.execute("SELECT title, price FROM items WHERE item_id = ?", (item_id,))
        item = await cursor.fetchone()
        if not item:
            await callback.answer("❌ Item not found.", show_alert=True)
            return
        title, price = item
        # Check balance
        cursor = await db.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = await cursor.fetchone()
        if not bal or bal[0] < price:
            await callback.answer("❌ Not enough balance.", show_alert=True)
            return
        # Get available inventory
        cursor = await db.execute("SELECT inventory_id, content FROM inventory WHERE item_id = ? AND sold = 0 LIMIT 1", (item_id,))
        inventory = await cursor.fetchone()
        if not inventory:
            await callback.answer("❌ Out of stock.", show_alert=True)
            return
        inventory_id, content = inventory
        # Process order
        await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (price, user_id))
        await db.execute("UPDATE inventory SET sold = 1, sold_to = ? WHERE inventory_id = ?", (user_id, inventory_id))
        await db.execute("UPDATE items SET stock = stock - 1 WHERE item_id = ?", (item_id,))
        await db.execute("INSERT INTO transactions (user_id, amount, type, status, created_at) VALUES (?, ?, ?, ?, ?)",
                         (user_id, price, "purchase", "success", datetime.datetime.now().isoformat()))
        await db.commit()
    await callback.message.answer(f"✅ Purchase successful! Here is your product:\n\n{content}")
    await callback.message.edit_text("📦 Purchase complete!", reply_markup=main_menu_kb())

@router.callback_query(F.data == "main_menu")
async def return_main(callback: CallbackQuery):
    await callback.message.edit_text("👋 Main Menu:", reply_markup=main_menu_kb())
