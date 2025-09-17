from aiogram import Router, types, F
from aiogram.filters import CommandStart
from bot.keyboards.registration import get_reg_kb, main_menu_kb
from bot.utils.database import is_user_in_team, is_user_registered   
from aiogram.fsm.context import FSMContext

router = Router()
    
@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    if not await is_user_registered(user_id):
        await message.answer(
            """
Хей! Я твій помічничок, який допоможе тобі:\n
🔧Дізнатися більше про BEST Engineering Competition
📝Зареєструватися на змагання
🤝Створити команду (або знайти, якщо її ще немає)
📡Дізнатися всю актуальну інформацію під час змагань
🚀Розпочати тестове завдання\n
У разі технічних чоколядок звертайся сюди: @vladlleen 
            """,
            reply_markup=get_reg_kb(),
            parse_mode="HTML"
        )
        return
    reply = main_menu_kb()
    await message.answer(
        "Знову привіт! 👋 Ви вже зареєстровані.",
        reply_markup=reply
    )

