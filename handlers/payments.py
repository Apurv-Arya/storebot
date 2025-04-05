from aiogram import Router, F, types
from aiogram.types import CallbackQuery, Message
from keyboards.inline import manual_methods_kb, topup_kb, main_menu_kb
from utils.config import ADMIN_IDS, PROOFS_CHANNEL_ID
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

@router.callback_query(F.data.startswith("method_"))
async def payment_method_selected(callback: CallbackQuery, state: FSMContext):
    method = callback.data.split("_")[1]

    if method == "back":
        return await callback.message.edit_text("Choose how you want to top up:", reply_markup=topup_method_kb())

    data = PAYMENT_METHODS.get(method)
    if not data:
        return await callback.answer("❌ Unknown payment method.")

    await state.update_data(payment_method=method)
    await state.set_state(TopUpState.waiting_for_proof)

    await callback.message.edit_text(
        f"{data['title']}\n\n"
        f"<b>Send payment to:</b>\n<code>{data['details']}</code>\n\n"
        "📩 After sending payment, reply with a screenshot or transaction ID here.",
        parse_mode="HTML"
    )
 
@router.message(PaymentProof.waiting_for_proof)
async def handle_payment_proof(message: Message, state: FSMContext):
    data = await state.get_data()
    method = data.get("payment_method")
    user = message.from_user

    text = (
        f"📥 <b>New Top-Up Request</b>\n"
        f"👤 User: @{user.username or 'N/A'} | <code>{user.id}</code>\n"
        f"💳 Method: <b>{method.upper()}</b>\n"
        f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    success = False

    # ✅ Forward to Admins
    for admin_id in ADMIN_IDS:
        try:
            if message.photo:
                await message.bot.send_photo(admin_id, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
            elif message.document:
                await message.bot.send_document(admin_id, document=message.document.file_id, caption=caption, parse_mode="HTML")
            elif message.text:
                await message.bot.send_message(admin_id, caption + message.text, parse_mode="HTML")
            success = True
        except Exception as e:
            print(f"❌ Error sending proof to admin {admin_id}: {e}")

    # ✅ Forward to Proofs Channel
    try:
        if message.photo:
            await message.bot.send_photo(PROOFS_CHANNEL_ID, photo=message.photo[-1].file_id, caption=caption, parse_mode="HTML")
        elif message.document:
            await message.bot.send_document(PROOFS_CHANNEL_ID, document=message.document.file_id, caption=caption, parse_mode="HTML")
        elif message.text:
            await message.bot.send_message(PROOFS_CHANNEL_ID, caption + message.text, parse_mode="HTML")
        success = True
    except Exception as e:
        print(f"❌ Error sending proof to channel: {e}")

    # ✅ Final response to user
    if success:
        await message.answer("✅ Your payment proof has been sent to our team.\nThey’ll review and update your balance soon.")
    else:
        await message.answer("❌ Failed to forward your proof. Please try again or contact support.")

@router.callback_query(F.data == "main_menu")
async def return_main_menu(callback: CallbackQuery):
    await callback.message.edit_text(text="👋 Main Menu:", reply_markup=main_menu_kb())
