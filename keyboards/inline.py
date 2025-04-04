from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Browse Store", callback_data="browse_store")],
        [InlineKeyboardButton(text="💰 Top-Up Balance", callback_data="topup_options")],
        [InlineKeyboardButton(text="💼 My Balance", callback_data="check_balance")]
    ])

def manual_methods_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 BinancePay", callback_data="method_binance")],
        [InlineKeyboardButton(text="💸 PayPal", callback_data="method_paypal")],
        [InlineKeyboardButton(text="🪙 Crypto", callback_data="method_crypto")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ])

def category_menu_kb(categories):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=cat[1], callback_data=f"cat_{cat[0]}")] for cat in categories
    ] + [[InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]])
