from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.handlers.about_event import AboutEventStates
from bot.keyboards.team import get_have_team_kb, get_back_kb
from bot.keyboards.no_team import get_category_kb, get_not_team_kb
from bot.utils.database import save_team_data, update_user_team, get_team_by_name
from uuid import uuid4
from aiogram.types import FSInputFile


router = Router()

class CreateTeam(StatesGroup):
    category = State()
    team_name = State()
    password = State()
    check_password = State()

@router.message(F.text == "⬅️ Назад")
async def process_back(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Ви повернулися до головного меню.", reply_markup=get_not_team_kb())

@router.message(F.text == "Створити команду🥇")
async def create_team(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(" Обери категорію змагань ", reply_markup=get_category_kb(with_back=True))
    await state.set_state(CreateTeam.category)

@router.message(CreateTeam.category)
async def process_category(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await process_back(message, state)
        return
    valid_categories = ["Team Design", "Innovative Design"]
    if message.text == "Детальніше про категорії":
        await message.answer("То що ж, познайомишся з нашими категоріями? А ще вони можуть співпрацювати🤫.\n\nInnovative Design\n\nКонцептуальна категорія, де ти з командою придумуєш нове або вдосконалене інженерне рішення для реальної проблеми. Ваше завдання – показати, як це працює: через креслення або 3D-моделі. Тут важлива креативність, інноваційність і реалістичність твоєї ідеї.\n\nTeam Design\n\nПрактична інженерна категорія, де ти з командою будеш розв'язувати технічні задачі – у стилі ось проблема – зробіть пристрій, який її вирішує. Електроніка, механіка, IoT, embedded – все це про Team Design. На виході – робочий прототип.", reply_markup=get_category_kb(with_back=True))
        return
    if message.text not in valid_categories:
        await message.answer("Будь ласка, оберіть одну з категорій: Team Design або Innovative Design.", reply_markup=get_category_kb(with_back=True))
        return
    await state.update_data(category=message.text)
    await message.answer(" Тепер введи назву команди ", reply_markup=get_back_kb())
    await state.set_state(CreateTeam.team_name)

@router.message(CreateTeam.team_name)
async def process_team_name(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    if message.text == "⬅️ Назад":
        # Повертаємося до вибору категорії
        await message.answer("Оберіть категорію:", reply_markup=get_category_kb(with_back=True))
        await state.set_state(CreateTeam.category)
        return
    # Перевірка унікальності імені команди
    existing_team = await get_team_by_name(message.text)
    if existing_team:
        await message.answer("Команда з такою назвою вже існує. Введіть іншу назву або натисніть 'Назад'.", reply_markup=get_back_kb())
        return
    await state.update_data(team_name=message.text)
    await message.answer("Гарна назва! Тепер створи пароль більше за 5 символів. Завдяки ньому інші учасники увійдуть в команду!", reply_markup=get_back_kb())
    await state.set_state(CreateTeam.password)

@router.message(CreateTeam.password)
async def process_team_password(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    if message.text == "⬅️ Назад":
        await message.answer("Введи технології, з якими працює команда (через кому):", reply_markup=get_back_kb())
        await state.set_state(CreateTeam.technologies)
        return
    if len(message.text) < 5:
        await message.answer("Пароль занадто короткий. Введи пароль більше за 5 символів:", reply_markup=get_back_kb())
        return
    await state.update_data(password=message.text)
    await message.answer("Підтверди пароль (напиши його заново)", reply_markup=get_back_kb())
    await state.set_state(CreateTeam.check_password)

@router.message(CreateTeam.check_password)
async def process_team_check_password(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    if message.text == "⬅️ Назад":
        await message.answer("Введи пароль для команди:", reply_markup=get_back_kb())
        await state.set_state(CreateTeam.password)
        return
    data = await state.get_data()
    if data["password"] != message.text:
        await message.answer("Неправильний пароль для команди. Спробуй ще раз:", reply_markup=get_back_kb())
        await state.set_state(CreateTeam.check_password)
        return

    team_id = str(uuid4())
    await save_team_data(
        team_id=team_id,
        team_name=data["team_name"],
        category=data["category"],
        password=data["password"],
        members_telegram_ids=[message.from_user.id]
    )

    await message.answer(
        f"Супер! Команду зареєстровано!",
        reply_markup=get_have_team_kb()
    )
    await update_user_team(user_id=message.from_user.id, team_id=team_id)

    await state.clear()
