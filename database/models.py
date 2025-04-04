import aiosqlite
from datetime import datetime

DB_PATH = "store.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            registered_at TEXT
        )''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            price REAL,
            stock INTEGER
        )''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            content TEXT,
            sold INTEGER DEFAULT 0,
            sold_to INTEGER DEFAULT NULL
        )''')
        await db.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            status TEXT,
            created_at TEXT
        )''')
        await db.commit()
