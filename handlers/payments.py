from aiogram import Router, F, types
from aiogram.types import CallbackQuery
from keyboards.inline import topup_kb
from utils.config import ADMIN_IDS

router = Router()

@router.callback_query(F.data == "topup_options")
async def topup(callback: CallbackQuery):
    await callback.message.edit_text(text="💰 Choose top-up method:", reply_markup=topup_kb())

@router.callback_query(F.data == "manual_topup")
async def manual(callback: CallbackQuery):
    admins = "\n".join([f"• [Admin](tg://user?id={admin})" for admin in ADMIN_IDS])
    await callback.message.edit_text(
        text=f"📩 Contact an admin to top-up your balance:\n\n{admins}",
        parse_mode="Markdown"
    )
