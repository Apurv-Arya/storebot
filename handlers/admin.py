from aiogram import Router, types, F
from database.db import DB_PATH
from utils.config import ADMIN_IDS
from aiogram.types import CallbackQuery
from keyboards.inline import inventory_remove_kb, bulk_remove_kb, edit_item_kb
import aiosqlite
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile

class EditItemStates(StatesGroup):
    choosing_field = State()
    editing_title = State()
    editing_price = State()
    editing_description = State()
    editing_category = State()

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
async def add_item(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")

    try:
        _, title, price, category, *desc = message.text.split(" ", 4)
        price = float(price)
        desc = desc[0] if desc else ""
    except:
        return await message.answer("⚠️ Usage:\n/additem <title> <price> <category> <description?>")

    async with aiosqlite.connect(DB_PATH) as db:
        cat_cursor = await db.execute("SELECT category_id FROM categories WHERE name = ?", (category,))
        cat = await cat_cursor.fetchone()
        if not cat:
            return await message.answer("❌ Category not found.")

        category_id = cat[0]
        await db.execute("""
            INSERT INTO items (title, price, stock, description, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (title, price, 0, desc, category_id))  # Stock is always initialized to 0
        await db.commit()

    await message.answer(f"✅ Item <b>{title}</b> added successfully with initial stock of 0.\n💾 Stock will update automatically when you upload inventory.", parse_mode="HTML")


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


@router.message(F.text.startswith("/edititem"))
async def edit_item_start(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only")

    try:
        _, item_id = message.text.split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /edititem <item_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT title, price, description FROM items WHERE item_id = ?", (item_id,))
        item = await cur.fetchone()

    if not item:
        return await message.answer("❌ Item not found.")

    await state.set_data({"item_id": item_id})
    await state.set_state(EditItemStates.choosing_field)

    await message.answer(
        f"📝 <b>Editing Item #{item_id}</b>\n\n"
        f"🏷️ <b>Title:</b> {item[0]}\n"
        f"💰 <b>Price:</b> ${item[1]:.2f}\n"
        f"📃 <b>Description:</b> {item[2]}\n",
        parse_mode="HTML",
        reply_markup=edit_item_kb(item_id)
    )

@router.callback_query(F.data.startswith("edit_title_"))
async def edit_title_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the new title:")
    await state.update_data(item_id=int(callback.data.split("_")[-1]))
    await state.set_state(EditItemStates.editing_title)

@router.callback_query(F.data.startswith("edit_price_"))
async def edit_price_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the new price (numbers only):")
    await state.update_data(item_id=int(callback.data.split("_")[-1]))
    await state.set_state(EditItemStates.editing_price)

@router.callback_query(F.data.startswith("edit_desc_"))
async def edit_description_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the new description:")
    await state.update_data(item_id=int(callback.data.split("_")[-1]))
    await state.set_state(EditItemStates.editing_description)

@router.callback_query(F.data.startswith("edit_cat_"))
async def edit_category_button(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Send the new category name:")
    await state.update_data(item_id=int(callback.data.split("_")[-1]))
    await state.set_state(EditItemStates.editing_category)

@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Edit canceled.")


@router.message(EditItemStates.editing_title)
async def set_new_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE items SET title = ? WHERE item_id = ?", (message.text, data['item_id']))
        await db.commit()
    await message.answer("✅ Title updated.")
    await state.clear()

@router.message(EditItemStates.editing_price)
async def set_new_price(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        price = float(message.text)
    except:
        return await message.answer("❌ Invalid price. Use numbers only.")
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE items SET price = ? WHERE item_id = ?", (price, data['item_id']))
        await db.commit()
    await message.answer("✅ Price updated.")
    await state.clear()

@router.message(EditItemStates.editing_description)
async def set_new_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE items SET description = ? WHERE item_id = ?", (message.text, data['item_id']))
        await db.commit()
    await message.answer("✅ Description updated.")
    await state.clear()

@router.message(EditItemStates.editing_category)
async def set_new_category(message: types.Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT category_id FROM categories WHERE name = ?", (message.text,))
        row = await cur.fetchone()
        if not row:
            return await message.answer("❌ Category not found.")
        await db.execute("UPDATE items SET category_id = ? WHERE item_id = ?", (row[0], data['item_id']))
        await db.commit()
    await message.answer("✅ Category updated.")
    await state.clear()

@router.message(F.text.startswith("/deleteitem"))
async def delete_item(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        _, item_id = message.text.strip().split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /deleteitem <item_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        # Check if item exists
        cur = await db.execute("SELECT title FROM items WHERE item_id = ?", (item_id,))
        row = await cur.fetchone()
        if not row:
            return await message.answer("❌ Item not found.")
        title = row[0]

        # Delete unsold inventory
        await db.execute("DELETE FROM inventory WHERE item_id = ? AND sold = 0", (item_id,))

        # Delete the item
        await db.execute("DELETE FROM items WHERE item_id = ?", (item_id,))
        await db.commit()

    await message.answer(f"🗑️ Item <b>{title}</b> (ID: {item_id}) and its unsold inventory have been deleted.", parse_mode="HTML")

@router.message(F.text.startswith("/cloneitem"))
async def clone_item(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        _, item_id = message.text.strip().split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /cloneitem <item_id>")

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT title, price, description, category_id
            FROM items
            WHERE item_id = ?
        """, (item_id,))
        item = await cursor.fetchone()

        if not item:
            return await message.answer("❌ Item not found.")

        title, price, description, category_id = item
        clone_title = f"{title} (Clone)"

        await db.execute("""
            INSERT INTO items (title, price, stock, description, category_id)
            VALUES (?, ?, ?, ?, ?)
        """, (clone_title, price, 0, description, category_id))

        await db.commit()

    await message.answer(f"🧬 Item <b>{title}</b> cloned successfully as <b>{clone_title}</b>.", parse_mode="HTML")


@router.message(F.text == "/importitems")
async def start_import(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")
    await message.answer("📂 Send a .csv or .txt file with item list in this format:\n\n`title,price,category,description`", parse_mode="Markdown")


@router.message(F.document)
async def handle_import_file(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    file = message.document
    if not file.file_name.endswith(".csv") and not file.file_name.endswith(".txt"):
        return await message.answer("❌ Please send a valid .csv or .txt file.")

    path = f"temp_{file.file_id}.txt"
    await message.bot.download(file, destination=path)

    count = 0
    skipped = 0

    async with aiosqlite.connect(DB_PATH) as db:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                parts = [x.strip() for x in line.strip().split(",")]
                if len(parts) < 3:
                    skipped += 1
                    continue

                title = parts[0]
                try:
                    price = float(parts[1])
                except:
                    skipped += 1
                    continue

                category = parts[2]
                description = parts[3] if len(parts) > 3 else ""

                # get category_id or skip
                cursor = await db.execute("SELECT category_id FROM categories WHERE name = ?", (category,))
                row = await cursor.fetchone()
                if not row:
                    skipped += 1
                    continue

                cat_id = row[0]
                await db.execute("""
                    INSERT INTO items (title, price, stock, description, category_id)
                    VALUES (?, ?, 0, ?, ?)
                """, (title, price, description, cat_id))
                count += 1

        await db.commit()

    import os
    os.remove(path)

    await message.answer(f"✅ Import complete.\n➕ Added: {count}\n⛔ Skipped: {skipped}")


@router.message(F.text.startswith("/importinv"))
async def start_inventory_import(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        _, item_id = message.text.strip().split()
        item_id = int(item_id)
    except:
        return await message.answer("⚠️ Usage: /importinv <item_id>")

    # Check if item exists
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT title FROM items WHERE item_id = ?", (item_id,))
        row = await cur.fetchone()
        if not row:
            return await message.answer("❌ Item not found.")

    await state.set_state("awaiting_inventory_file")
    await state.update_data(item_id=item_id)
    await message.answer(f"📥 Now send a `.txt` or `.csv` file with inventory content.\nEach line = 1 inventory unit.", parse_mode="Markdown")


@router.message(F.document)
async def import_inventory_file(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state != "awaiting_inventory_file":
        return  # ignore other uploads not in import mode
async def import_inventory_file(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    item_id = data.get("item_id")
    await state.clear()

    file = message.document
    if not file.file_name.endswith(".txt") and not file.file_name.endswith(".csv"):
        return await message.answer("❌ Please send a `.txt` or `.csv` file.")

    path = f"temp_inv_{file.file_id}.txt"
    await message.bot.download(file, destination=path)

    added = 0
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    async with aiosqlite.connect(DB_PATH) as db:
        for content in lines:
            await db.execute("INSERT INTO inventory (item_id, content) VALUES (?, ?)", (item_id, content))
        await db.execute("UPDATE items SET stock = stock + ? WHERE item_id = ?", (len(lines), item_id))
        await db.commit()

    import os
    os.remove(path)

    await message.answer(f"✅ Inventory import complete.\n🧾 Added {len(lines)} units to item ID {item_id}.")


@router.message(F.text == "/idlist")
async def show_all_ids(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    try:
        msg = "<b>📦 {STOREBOT_NAME} ID Summary</b>\n\n"

        async with aiosqlite.connect(DB_PATH) as db:

            # Categories
            msg += "📁 <b>Categories:</b>\n"
            cur = await db.execute("SELECT category_id, name FROM categories")
            cats = await cur.fetchall()
            if cats:
                for cid, name in cats:
                    msg += f"• ID: <code>{cid}</code> → {name}\n"
            else:
                msg += "❌ No categories found.\n"

            # Items
            msg += "\n🛍️ <b>Items:</b>\n"
            cur = await db.execute("SELECT item_id, title, price FROM items")
            items = await cur.fetchall()
            if items:
                for iid, title, price in items:
                    msg += f"• ID: <code>{iid}</code> → {title} (${price:.2f})\n"
            else:
                msg += "❌ No items found.\n"

            # Inventory
            msg += "\n📦 <b>Inventory (Top 10):</b>\n"
            cur = await db.execute("""
                SELECT inventory_id, item_id, sold
                FROM inventory
                ORDER BY inventory_id DESC
                LIMIT 10
            """)
            inv = await cur.fetchall()
            if inv:
                for inv_id, item_id, sold in inv:
                    status = "✅ Sold" if sold else "🟢 Available"
                    msg += f"• ID: <code>{inv_id}</code> → Item {item_id} ({status})\n"
            else:
                msg += "❌ No inventory entries.\n"

        # Telegram max message length protection
        if len(msg) > 4000:
            msg = msg[:3990] + "\n\n⚠️ Output truncated due to message length."

        await message.answer(msg, parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Error generating ID list:\n<code>{e}</code>", parse_mode="HTML")

@router.message(F.text == "/dashboard")
async def analytics_dashboard(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admin only.")

    async with aiosqlite.connect(DB_PATH) as db:
        # Total sales
        cur = await db.execute(
            "SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM transactions WHERE type LIKE 'purchase%' AND status = 'success'"
        )
        total_sales, tx_count = await cur.fetchone()

        # Total users
        cur = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cur.fetchone())[0]

        # Top-selling items
        cur = await db.execute("""
            SELECT i.title, COUNT(*) as count
            FROM inventory inv
            JOIN items i ON i.item_id = inv.item_id
            WHERE inv.sold = 1
            GROUP BY inv.item_id
            ORDER BY count DESC
            LIMIT 5
        """)
        item_stats = await cur.fetchall()

        # Top buyers
        cur = await db.execute("""
            SELECT u.username, COUNT(*) as count
            FROM transactions t
            JOIN users u ON u.user_id = t.user_id
            WHERE t.type LIKE 'purchase%' AND t.status = 'success'
            GROUP BY t.user_id
            ORDER BY count DESC
            LIMIT 5
        """)
        buyers = await cur.fetchall()

        # Revenue past 7 days
        cur = await db.execute("""
            SELECT date(created_at), SUM(amount)
            FROM transactions
            WHERE type LIKE 'purchase%' AND status = 'success'
              AND created_at >= date('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY date(created_at) DESC
        """)
        week_stats = await cur.fetchall()

    # Build response
    text = f"<b>📊 {STOREBOT_NAME} Analytics Dashboard</b>\n\n"
    text += f"🛒 <b>Total Sales:</b> ${total_sales:.2f} ({tx_count} orders)\n"
    text += f"👥 <b>Total Users:</b> {total_users}\n\n"

    text += "🏆 <b>Top-Selling Items:</b>\n"
    if item_stats:
        for title, count in item_stats:
            text += f"• {title} – {count} sales\n"
    else:
        text += "• No sales yet\n"

    text += "\n👤 <b>Top Buyers:</b>\n"
    if buyers:
        for username, count in buyers:
            user_disp = f"@{username}" if username else "User"
            text += f"• {user_disp} – {count} orders\n"
    else:
        text += "• No buyers yet\n"

    text += "\n📅 <b>Last 7 Days Revenue:</b>\n"
    if week_stats:
        for date, amt in week_stats:
            text += f"• {date} – ${amt:.2f}\n"
    else:
        text += "• No recent revenue\n"

    await message.answer(text, parse_mode="HTML")


@router.message(F.text.startswith("/delcat"))
async def delete_category(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("🔒 Admins only.")

    try:
        _, category_name = message.text.strip().split(maxsplit=1)
    except:
        return await message.answer("⚠️ Usage: /delcat <category_name>")

    async with aiosqlite.connect(DB_PATH) as db:
        # Find category ID
        cur = await db.execute("SELECT category_id FROM categories WHERE name = ?", (category_name,))
        row = await cur.fetchone()
        if not row:
            return await message.answer("❌ Category not found.")

        cat_id = row[0]

        # Find item IDs under this category
        cur = await db.execute("SELECT item_id FROM items WHERE category_id = ?", (cat_id,))
        items = await cur.fetchall()
        item_ids = [item_id for (item_id,) in items]

        # Delete all inventory tied to those items
        for item_id in item_ids:
            await db.execute("DELETE FROM inventory WHERE item_id = ?", (item_id,))

        # Delete the items themselves
        await db.execute("DELETE FROM items WHERE category_id = ?", (cat_id,))
        # Delete the category
        await db.execute("DELETE FROM categories WHERE category_id = ?", (cat_id,))
        await db.commit()

    await message.answer(f"✅ Category <b>{category_name}</b> and all related items/inventory have been deleted.", parse_mode="HTML")
