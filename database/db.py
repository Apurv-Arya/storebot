import aiosqlite

DB_PATH = "store.db"

async def safe_alter_column():
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("ALTER TABLE users ADD COLUMN username TEXT;")
            await db.commit()
        except aiosqlite.OperationalError as e:
            if "duplicate column" not in str(e).lower():
                raise  # real error


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0,
            registered_at TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            description TEXT,
            price REAL,
            stock INTEGER,
            category_id INTEGER
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            inventory_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            content TEXT,
            sold INTEGER DEFAULT 0,
            sold_to INTEGER
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            type TEXT,
            status TEXT,
            created_at TEXT
        )""")
        await db.commit()
