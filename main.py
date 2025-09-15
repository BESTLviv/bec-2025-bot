import asyncio
from dotenv import load_dotenv
load_dotenv()
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from bot.admin import admin_start
from config import load_config
from bot.middleware.check_user import AuthMiddleware
from bot.handlers import cv, registration, start, main_menu, create_team, team, about_event, find_team, create_cv
from bot.utils.database import get_database

config = load_config()

if not config.bot_token:
    raise ValueError("BOT_TOKEN не знайдено! Перевірте ваш .env файл.")

bot = Bot(token=config.bot_token) 
dp = Dispatcher(storage=MemoryStorage())


async def main():
    bot.session.default_parse_mode = "HTML"
    db = await get_database()
    
    dp.message.middleware(AuthMiddleware(db))
    
    dp.include_routers(
        start.router,
        about_event.router,
        registration.router,
        main_menu.router,
        create_team.router,
        find_team.router,
        team.router,
        cv.router,
        create_cv.router,
        admin_start.router
    )
    
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Помилка сталася: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())