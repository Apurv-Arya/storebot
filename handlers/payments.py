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
    await state.set_state(PaymentProof.selecting_method)
    await callback.message.edit_text(
        "💳 Choose a payment method:", reply_markup=manual_methods_kb()
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

@router.callback_query(F.data.startswith("method_"))
async def payment_method_selected(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]
    await state.update_data(method=method)
    await state.set_state(PaymentProof.waiting_for_proof)

    await callback.message.edit_text(
        f"📩 You selected <b>{method.title()}</b>.\n\nPlease send your payment proof (receipt/screenshot).",
        parse_mode="HTML"
    )
    await state.set_state(PaymentStates.waiting_for_proof)

@router.message(PaymentProof.waiting_for_proof)
async def handle_payment_proof(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = await state.get_data()
    method = data.get("method", "unknown").title()
    await state.clear()

    caption = (
        f"🧾 <b>New Payment Proof</b>\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"💳 Method: <b>{method}</b>\n"
    )

    sent = False
    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                await message.bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif message.document:
                await message.bot.send_document(admin_id, document=message.document.file_id, caption=caption, parse_mode="HTML")
            else:
                await message.bot.send_message(admin_id, caption + message.text, parse_mode="HTML")
            sent = True
        except Exception as e:
            print(f"❌ Failed to send to admin {admin_id}: {e}")

    if sent:
        await message.answer("✅ Your proof has been sent to our admins. You'll be credited once reviewed.")
    else:
        await message.answer("❌ Failed to forward your proof. Please try again later.")


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
