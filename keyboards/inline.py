from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Browse Store", callback_data="browse_store")],
        [InlineKeyboardButton(text="💰 Top-Up Balance", callback_data="topup_options")],
        [InlineKeyboardButton(text="💼 My Balance", callback_data="check_balance")]
    ])

def topup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Manual Top-Up", callback_data="manual_topup")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ])

def category_menu_kb(categories):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories
    ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]])
