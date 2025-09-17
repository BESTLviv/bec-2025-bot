from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.no_team import get_not_team_kb
from bot.keyboards.team import get_back_kb, get_have_team_kb
from bot.utils.database import get_team_by_name, add_user_to_team, is_full_team

router = Router()

class FindTeam(StatesGroup):
    team_name = State()
    password = State()

@router.message(F.text == "Увійти в команду🏅")
async def find_team_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Спочатку напиши назву команди", reply_markup=get_back_kb())
    await state.set_state(FindTeam.team_name)

@router.message(FindTeam.team_name)
async def process_team_name(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Ви повернулися до головного меню.", reply_markup=get_not_team_kb())
        return
    team = await get_team_by_name(message.text)
    if not team:
        await message.answer("Команду не знайдено. Введіть назву ще раз або натисніть 'Назад'.", reply_markup=get_back_kb())
        return
    await state.update_data(team=team)
    await message.answer(f"Тепер введи пароль, для входу в команду {team['team_name']}", reply_markup=get_back_kb())
    await state.set_state(FindTeam.password)

@router.message(FindTeam.password)
async def process_team_password(message: types.Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        await state.clear()
        await message.answer("Ви повернулися до головного меню.", reply_markup=get_not_team_kb())
        return
    data = await state.get_data()
    team = data.get("team")
    if not team or message.text != team["password"]:
        await message.answer("Неправильний пароль. Спробуйте ще раз або натисніть 'Назад'.", reply_markup=get_back_kb())
        return
    if await is_full_team(team["team_id"]):
        await message.answer("Вибач, але в цій команді вже 4 учасники. Спробуй приєднатися до іншої команди або створи свою.", reply_markup=get_not_team_kb())
        await state.clear()
        return
    await add_user_to_team(message.from_user.id, team["team_id"])
    await message.answer(f"Вітаю в команді {team['team_name']}!", reply_markup=get_have_team_kb())
    await state.clear()
