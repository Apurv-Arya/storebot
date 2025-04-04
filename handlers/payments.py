from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from keyboards.inline import topup_kb, main_menu_kb
from utils.config import ADMIN_IDS
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

class PaymentStates(StatesGroup):
    waiting_for_proof = State()


router = Router()


# FSM for receiving payment proof
class PaymentProof(StatesGroup):
    selecting_method = State()
    waiting_for_proof = State()

@router.callback_query(F.data == "topup_options")
async def topup_options(callback: CallbackQuery):
    await callback.message.edit_text("💰 Choose top-up method:", reply_markup=topup_kb())

@router.callback_query(F.data == "manual_topup")
async def manual_topup(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📩 Please send your payment proof (screenshot, receipt, or message).",
        reply_markup=topup_kb()
    )
    await state.set_state(PaymentProof.waiting_for_proof)

@router.message(PaymentProof.waiting_for_proof)
async def handle_payment_proof(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()

    caption = f"🧾 <b>New Payment Proof</b>\nFrom User: <code>{user_id}</code>\n"

    success = False
    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                await message.bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif message.document:
                await message.bot.send_document(admin_id, document=message.document.file_id, caption=caption, parse_mode="HTML")
            else:
                await message.bot.send_message(admin_id, caption + message.text, parse_mode="HTML")
            success = True
        except Exception as e:
            print(f"⚠️ Failed to forward to admin {admin_id}: {e}")

    if success:
        await message.answer("✅ Payment proof sent to admins. You'll be credited once reviewed.")
    else:
        await message.answer("❌ Failed to deliver proof. Please try again or contact admin.")
        

@router.callback_query(F.data == "manual_topup")
async def manual_topup(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📩 Please send your payment proof (photo, screenshot, or text).\n\n"
        "Once received, an admin will review it manually.",
        reply_markup=topup_kb()
    )
    await state.set_state(PaymentStates.waiting_for_proof)

@router.message(PaymentStates.waiting_for_proof)
async def handle_proof(message: types.Message, state: FSMContext):
    await state.clear()
    forward_text = f"🧾 <b>New Payment Proof</b>\nFrom User: <code>{message.from_user.id}</code>\n"
    sent = False

    for admin in ADMIN_IDS:
        try:
            if message.photo:
                await message.bot.send_photo(admin, message.photo[-1].file_id, caption=forward_text, parse_mode="HTML")
            elif message.document:
                await message.bot.send_document(admin, message.document.file_id, caption=forward_text, parse_mode="HTML")
            else:
                await message.bot.send_message(admin, forward_text + "\n" + message.text, parse_mode="HTML")
            sent = True
        except Exception as e:
            print(f"Failed to send proof to admin {admin}: {e}")

    if sent:
        await message.answer("✅ Payment proof sent to admin. You'll be notified once your balance is updated.")
    else:
        await message.answer("❌ Failed to send proof to admins. Please try again or contact them directly.")

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

@router.callback_query(F.data == "main_menu")
async def return_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(text="👋 Main Menu:", reply_markup=main_menu_kb())
