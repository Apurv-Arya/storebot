from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Browse Store", callback_data="browse_store")],
        [InlineKeyboardButton(text="💰 Top-Up Balance", callback_data="topup_options")],
        [InlineKeyboardButton(text="💼 My Balance", callback_data="check_balance")],
    ])

def topup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📩 Manual (Contact Admin)", callback_data="manual_topup")],
        [InlineKeyboardButton(text="🪙 Crypto (CoinPayments)", callback_data="crypto_topup")],
    ])

def store_item_kb(item_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Buy Now", callback_data=f"buy_{item_id}")],
    ])
