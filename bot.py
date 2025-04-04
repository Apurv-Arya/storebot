from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from database.db import init_db
from utils.config import BOT_TOKEN
from handlers import user, admin, payments

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

async def main():
    await init_db()
    dp.include_router(user.router)
    dp.include_router(admin.router)
    dp.include_router(payments.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
