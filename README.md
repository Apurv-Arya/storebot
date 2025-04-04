# 🛍️ Telegram StoreBot

A fully-featured Telegram bot built in **Python** using `aiogram 3.x`, that acts as a **digital goods store** with wallet, categories, auto delivery, admin panel, and manual top-up with proof verification.

---

## ⚙️ Features

✅ User Wallet (Balance)  
✅ Auto Delivery of Purchased Items  
✅ Item listings show real-time stock on store💼
✅ Admin Panel with Item Upload and Inventory  
✅ Product Categories 📂  
✅ Manual Top-Up + Payment Method Selection  
✅ Payment Proof Upload (sent to Admins + Channel)  
✅ Inline Product Search 🔍  
✅ Paginated Category Browsing 🔁  
✅ /info – Show user ID, balance, username  
✅ /myorders – Show purchased items  
✅ /resend – Resend purchased items  
✅ Admin Stats: `/stats`, `/userstats`, `/txhistory`, `/setbalance`
✅ Auto-alerts to all Admins when any item stock hits 2 or 1
✅ Alerts include: item name + stock count
✅ No manual monitoring needed

---

## 📦 Project Structure
storebot/
├── bot.py 
├── .env 
├── requirements.txt 
├── README.md 
├── database/ 
│ └── db.py 
├── handlers/ 
│ ├── user.py 
│ ├── admin.py 
│ ├── payments.py 
├── keyboards/ 
│ └── inline.py 
├── utils/ 
│ └── config.py


---

## 🧰 Installation Instructions

### ✅ Prerequisites

- Python 3.10+  
- Telegram Bot Token (from @BotFather)  
- A private Telegram channel (for payment proofs logging)  
- A list of Bot Admins Telegram usernames

---

### 🔧 Setup Steps

1. **Clone the repo** (or copy files into your project)

2. **Install dependencies**:

```bash
pip install -r requirements.txt

3. **Create .env file in the root**:
BOT_TOKEN="your_bot_token"
ADMIN_IDS="username,username"
PROOFS_CHANNEL_ID="-1001234567890"

```bash
python bot.py


💬 User Commands
Command	Description
/start	Welcome message + main menu
/info	Show Telegram ID, username, balance
/myorders	Show latest 10 purchases
/resend <item>	Re-deliver previous product

🔐 Admin Commands
Command	Description
/addcat <name>	Add a new category
/additem <title> <price> <stock> <category> <desc?>	Add product
/upload <item_id>	Reply to message to upload digital content
/setbalance <uid> <amount>	Manually adjust user wallet
/stats	Show total orders and revenue
/userstats <uid>	Show spending and order count for a user
/txhistory <uid>	Show last 10 transactions of user

📩 Payment Flow
1.User taps Top-Up Balance
2.Selects payment method (Crypto, Bank, PayPal, etc.)
3.Sends screenshot or receipt
4.Bot forwards proof to:
  All Admins
  Central channel (PROOFS_CHANNEL_ID)

5.Admin credits balance via /setbalance

🛡️ Notes
Bot must be admin in PROOFS_CHANNEL_ID
All proofs and transactions are private
Works out-of-the-box with SQLite (no setup needed)


