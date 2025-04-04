from aiogram import Router, types, F
from database.db import DB_PATH
from utils.config import ADMIN_IDS
from keyboards.inline import inventory_remove_kb
from keyboards.inline import bulk_remove_kb
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
async def upload_content(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /upload <item_id> (reply to content)")

    if not message.reply_to_message:
        return await message.answer("📎 Reply to the content you want to upload.")

    # Get content from reply (text or document)
    content = message.reply_to_message.text or message.reply_to_message.document.file_id
    if not content:
        return await message.answer("❌ No valid content found in reply.")

    async with aiosqlite.connect(DB_PATH) as db:
        # Insert content into inventory
        await db.execute("INSERT INTO inventory (item_id, content) VALUES (?, ?)", (item_id, content))

        # Auto-update stock count for item
        await db.execute("UPDATE items SET stock = stock + 1 WHERE item_id = ?", (item_id,))
        await db.commit()

    await message.answer("✅ Content uploaded and stock updated automatically.")


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

@router.message(F.text.startswith("/inventory"))
async def view_item_inventory(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /inventory <item_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        # Get item title
        cursor = await db.execute("SELECT title FROM items WHERE item_id = ?", (item_id,))
        item = await cursor.fetchone()
        if not item:
            return await message.answer("❌ Item not found.")

        title = item[0]
        # Get unsold inventory
        cursor = await db.execute("""
            SELECT inventory_id, content
            FROM inventory
            WHERE item_id = ? AND sold = 0
            LIMIT 10
        """, (item_id,))
        contents = await cursor.fetchall()

    if not contents:
        return await message.answer(f"📦 No unsold inventory found for <b>{title}</b>.", parse_mode="HTML")

    msg = f"📦 <b>Unsold Inventory for: {title}</b>\n\n"
    for inv_id, content in contents:
        msg += f"• <code>{content}</code>\n"

    await message.answer(msg, parse_mode="HTML")


@router.message(F.text.startswith("/removeinv"))
async def remove_inventory_list(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /removeinv <item_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT title FROM items WHERE item_id = ?", (item_id,))
        item = await cur.fetchone()
        if not item:
            return await message.answer("❌ Item not found.")
        title = item[0]

        cur = await db.execute("""
            SELECT inventory_id, content
            FROM inventory
            WHERE item_id = ? AND sold = 0
            LIMIT 10
        """, (item_id,))
        items = await cur.fetchall()

    if not items:
        return await message.answer(f"📦 No unsold inventory for <b>{title}</b>.", parse_mode="HTML")

    for inv_id, content in items:
        await message.answer(
            f"🧾 <b>{title}</b> Inventory #{inv_id}:\n<code>{content}</code>",
            reply_markup=inventory_remove_kb(item_id, inv_id),
            parse_mode="HTML"
        )
        

@router.callback_query(F.data.startswith("removeinv_"))
async def delete_inventory(callback: CallbackQuery):
    data = callback.data.split("_")
    item_id = int(data[1])
    inv_id = int(data[2])

    async with aiosqlite.connect(DB_PATH) as db:
        # Ensure it exists
        cursor = await db.execute("SELECT content FROM inventory WHERE inventory_id = ? AND sold = 0", (inv_id,))
        item = await cursor.fetchone()
        if not item:
            return await callback.answer("❌ Already sold or doesn't exist.")

        # Delete inventory and decrement stock
        await db.execute("DELETE FROM inventory WHERE inventory_id = ?", (inv_id,))
        await db.execute("UPDATE items SET stock = stock - 1 WHERE item_id = ?", (item_id,))
        await db.commit()

    await callback.message.edit_text("✅ Inventory content removed and stock updated.")
    await callback.answer("Removed.")


@router.message(F.text.startswith("/uploadbulk"))
async def bulk_upload(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")
    
    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /uploadbulk <item_id> (then reply with lines of codes)")

    if not message.reply_to_message:
        return await message.answer("📎 Please reply to the command with content list.")

    content = message.reply_to_message.text
    if not content:
        return await message.answer("❌ No text found in reply.")

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return await message.answer("⚠️ No valid content lines found.")

    async with aiosqlite.connect(DB_PATH) as db:
        for line in lines:
            await db.execute("INSERT INTO inventory (item_id, content) VALUES (?, ?)", (item_id, line))
        await db.execute("UPDATE items SET stock = stock + ? WHERE item_id = ?", (len(lines), item_id))
        await db.commit()

    await message.answer(f"✅ {len(lines)} items uploaded to inventory and stock updated.")


@router.message(F.text.startswith("/bulkremove"))
async def bulk_remove_start(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")
    
    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /bulkremove <item_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT inventory_id, content
            FROM inventory
            WHERE item_id = ? AND sold = 0
            LIMIT 20
        """, (item_id,))
        items = await cursor.fetchall()

    if not items:
        return await message.answer("📭 No unsold inventory available.")

    text = "🗑️ <b>Select inventory to remove</b>:\n\n"
    for inv_id, content in items:
        msg += f"• <code>{content}</code>\n"

    inv_ids = [inv_id for inv_id, _ in items]
    await message.answer(text, reply_markup=bulk_remove_kb(item_id, inv_ids), parse_mode="HTML")


@router.callback_query(F.data.startswith("bulkdel_"))
async def handle_bulk_remove(callback: CallbackQuery):
    data = callback.data.split("_")
    if len(data) != 3:
        return await callback.answer("❌ Invalid data.")

    _, item_id_str, inv_id_str = data

    try:
        item_id = int(item_id_str)
        inv_id = int(inv_id_str)
    except ValueError:
        return await callback.answer("❌ Invalid IDs.")

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if inventory exists and is unsold
        cur = await db.execute("SELECT content FROM inventory WHERE inventory_id = ? AND sold = 0", (inv_id,))
        result = await cur.fetchone()

        if not result:
            return await callback.answer("❌ Already sold or doesn't exist.")

        # Delete and update stock
        await db.execute("DELETE FROM inventory WHERE inventory_id = ?", (inv_id,))
        await db.execute("UPDATE items SET stock = stock - 1 WHERE item_id = ?", (item_id,))
        await db.commit()

    await callback.answer("✅ Inventory removed.")
    await callback.message.edit_text("✅ Inventory content removed and stock updated.")



