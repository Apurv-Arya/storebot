from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🛍 Browse Store", callback_data="browse_store")],
        [InlineKeyboardButton("💰 Top-Up Balance", callback_data="topup_options")],
        [InlineKeyboardButton("💼 My Balance", callback_data="check_balance")],
    ])

def topup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
<<<<<<< HEAD
        [InlineKeyboardButton("📩 Contact Admin", callback_data="manual_topup")],
        [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
=======
        [InlineKeyboardButton(text="📩 Contact Admin for Top-Up", callback_data="manual_topup")],
>>>>>>> eeb6dc4934705509cc99ca8b9914dfe7dfa919bc
    ])

def category_menu_kb(categories):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories
    ] + [[InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]])
