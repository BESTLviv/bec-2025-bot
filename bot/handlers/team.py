from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from bot.utils.database import get_team, exit_team, get_team_category
from bot.keyboards.no_team import get_not_team_kb

router = Router()

class Team(StatesGroup):
    waiting_for_stack_input = State()

@router.message(F.text == "Інформація про командуℹ️")
async def info_team_handler(message: types.Message, state: FSMContext):
    from bot.utils.database import users_collection
    user_id = message.from_user.id
    team = await get_team(user_id)
    if team:
        member_ids = team.get("members", [])
        usernames = []
        if member_ids:
            member = users_collection.find({"_id": {"$in": member_ids}})
            async for user in member:
                username = user.get("username")
                name = user.get("name")
                if username:
                    usernames.append(f"@{username}")
                elif name:
                    usernames.append(name)
                else:
                    usernames.append("Без імені")
        members_str = ", ".join(usernames) if usernames else "Немає учасників"
        await message.answer(
            f"Команда '{team['team_name']}'!\n\n"
            f"Категорія: {team['category']}\n\n"
            f"Учасники: {members_str}",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "Технічна помилка, спробуйте пізніше",
            parse_mode="HTML"
        )

@router.message(F.text == "Вийти з команди🚪")
async def exit_team_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await exit_team(user_id):
        await message.answer(
            "Успішно вийшли з команди",
            parse_mode="HTML",
            reply_markup=get_not_team_kb()
        )
    else:
        await message.answer(
            "Технічна помилка, спробуйте пізніше",
            parse_mode="HTML"
        )
        
@router.message(F.text == "Тестове завдання")
async def test_task_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if await get_team_category(user_id) == "Innovative Design":
        await message.answer(
            "Тестове завдання для категорії 'Innovative Design' наразі недоступне. Слідкуйте за оновленнями.",
            parse_mode="HTML",
        )
    if await get_team_category(user_id) == "Team Design":
        await message.answer(
            "Тестове завдання для категорії 'Team Design' наразі недоступне. Слідкуйте за оновленнями.",
            parse_mode="HTML",
        )
    else:
        await message.answer(
            "Технічна помилка, спробуйте пізніше",
            parse_mode="HTML"
        )
