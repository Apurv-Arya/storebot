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
