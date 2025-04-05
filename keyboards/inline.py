from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🛍 Browse Store", callback_data="browse_store")
    ],
    [
        InlineKeyboardButton(text="📋 My Info", callback_data="menu_info"),
        InlineKeyboardButton(text="📦 My Orders", callback_data="menu_orders")
    ],
    [
        InlineKeyboardButton(text="💰 Top-Up Balance", callback_data="topup_options"),
        InlineKeyboardButton(text="💼 My Balance", callback_data="check_balance")
    ]])

def topup_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Payment Methods", callback_data="manual_topup")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
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

def inventory_remove_kb(item_id, inventory_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Remove", callback_data=f"removeinv_{item_id}_{inventory_id}")],
        [InlineKeyboardButton(text="⬅️ Back", callback_data="main_menu")]
    ])

def bulk_remove_kb(item_id, inventory_list):
    kb = [
        [InlineKeyboardButton(f"❌ {inv_id}", callback_data=f"bulkdel_{item_id}_{inv_id}")]
        for inv_id in inventory_list
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb + [[
        InlineKeyboardButton(text="⬅️ Done", callback_data="main_menu")
    ]])

def edit_item_kb(item_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏷️ Title", callback_data=f"edit_title_{item_id}")],
        [InlineKeyboardButton(text="💰 Price", callback_data=f"edit_price_{item_id}")],
        [InlineKeyboardButton(text="📃 Description", callback_data=f"edit_desc_{item_id}")],
        [InlineKeyboardButton(text="📁 Category", callback_data=f"edit_cat_{item_id}")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_edit")]
    ])

