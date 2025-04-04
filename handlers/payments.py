from aiogram import Router, types, F
from keyboards.inline import topup_kb
from utils.config import ADMIN_IDS
from aiogram.types import CallbackQuery
from utils.coinpayments import CoinPaymentsAPI
import random
from database.models import DB_PATH
import aiosqlite

router = Router()

@router.callback_query(F.data == "topup_options")
async def show_topup(callback: CallbackQuery):
    await callback.message.edit_text("💰 Choose top-up method:", reply_markup=topup_kb())

@router.callback_query(F.data == "manual_topup")
async def manual_topup(callback: CallbackQuery):
    admin_links = "\n".join([f"• @{admin_id}" for admin_id in ADMIN_IDS])
    await callback.message.edit_text(
        f"📩 To top up manually, contact an admin:\n\n{admin_links}",
        reply_markup=topup_kb()
    )

@router.callback_query(F.data == "crypto_topup")
async def crypto_topup(callback: CallbackQuery):
    # CoinPayments invoice logic coming in next block...
    await callback.message.edit_text("🔄 Generating crypto invoice... Please wait.")

@router.callback_query(F.data == "crypto_topup")
async def crypto_topup(callback: CallbackQuery):
    user_id = callback.from_user.id
    amount = 10 + random.randint(0, 10)  # for demo purposes, static $10–$20
    cp = CoinPaymentsAPI()
    result = cp.create_transaction(amount)

    if result.get("error") == "ok":
        txn = result["result"]
        address = txn["address"]
        amount_crypto = txn["amount"]
        checkout_url = txn["checkout_url"]
        currency = txn["coin"]

        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("INSERT INTO transactions (user_id, amount, type, status, created_at) VALUES (?, ?, ?, ?, ?)",
                             (user_id, amount, "crypto", "pending", datetime.datetime.now().isoformat()))
            await db.commit()

        await callback.message.edit_text(
            f"🪙 Send exactly `{amount_crypto}` **{currency}** to:\n`{address}`\n\n"
            f"🔗 [Pay now]({checkout_url})",
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    else:
        await callback.message.edit_text("❌ Failed to create invoice. Try again later.")
