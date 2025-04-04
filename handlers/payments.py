from aiogram import Router, types, F
from aiogram.types import CallbackQuery
from keyboards.inline import topup_kb
from utils.config import ADMIN_IDS
<<<<<<< HEAD
=======
from aiogram.types import CallbackQuery
import random
from database.models import DB_PATH
import aiosqlite
>>>>>>> eeb6dc4934705509cc99ca8b9914dfe7dfa919bc

router = Router()

@router.callback_query(F.data == "topup_options")
async def topup_options(callback: CallbackQuery):
    await callback.message.edit_text("💰 Choose top-up method:", reply_markup=topup_kb())

@router.callback_query(F.data == "manual_topup")
async def manual_topup(callback: CallbackQuery):
    admins = "\n".join([f"• [Admin](tg://user?id={aid})" for aid in ADMIN_IDS])
    await callback.message.edit_text(
        f"📩 To top up manually, message an admin:\n\n{admins}",
        parse_mode="Markdown", reply_markup=topup_kb()
    )
