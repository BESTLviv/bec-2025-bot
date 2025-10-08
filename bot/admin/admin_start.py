from email.mime import message
import os
from aiogram import Router, types, F
from bot.admin.admin_keyboard import get_admin_kb, get_statistic_kb
from dotenv import load_dotenv
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re
import html
from aiogram.exceptions import TelegramForbiddenError
from bot.utils.database import get_all_teams, get_all_user_ids, get_all_users_with_cv

load_dotenv()
router = Router()

@router.message(F.text == os.getenv("ADMIN_START"))
async def admin_start(message: types.Message):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id == admin_id:
        await message.answer(
            "Привіт, ADMIN!",
            reply_markup=get_admin_kb(),
            parse_mode="HTML"
        )
    return

class SpamStates(StatesGroup):
  waiting_for_message = State()

@router.message(F.text == "Розсилка")
async def start_spam(message: types.Message, state: FSMContext):
  admin_id = int(os.getenv("ADMIN_ID"))
  if message.from_user.id == admin_id:
    await message.answer("Введіть текст розсилки або 'Назад' для відміни:")
    await state.set_state(SpamStates.waiting_for_message)

@router.message(F.text == "Отримати всі CV")
async def get_all_cvs(message: types.Message):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    users_cursor = await get_all_users_with_cv()
    users = await users_cursor.to_list(length=None)

    if not users:
        await message.answer("Немає завантажених CV.")
        return

    for user in users:
        file_id = user.get("cv_file_path")
        username = user.get("username", "невідомо")
        user_id = user.get("telegram_id", "null")

        if file_id:
            await message.answer_document(
                document=file_id,
                caption=f"username: {username}\nid: {user_id}"
            )

@router.message(SpamStates.waiting_for_message)
async def send_spam(message: types.Message, state: FSMContext, bot):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    if message.text.lower() == "назад":
        await message.answer("Розсилку скасовано.", reply_markup=get_admin_kb())
        await state.clear()
        return

    raw_text = message.text or ""

    # Шукаємо посилання в тексті
    url_regex = re.compile(r'https?://t\.me/[^\s)]+')
    matches = list(url_regex.finditer(raw_text))

    if matches:
        first_match = matches[0]
        url = first_match.group(0)

        # Текст до посилання
        before_text = html.escape(raw_text[:first_match.start()])
        # Текст після посилання
        after_text = html.escape(raw_text[first_match.end():])

        # Створюємо фінальний текст з HTML-посиланням
        formatted_text = f'{before_text}<a href="{url}">Приєднатися</a>{after_text}'
    else:
        # Якщо посилань немає, просто екрануємо весь текст
        formatted_text = html.escape(raw_text)

    user_ids = await get_all_user_ids()
    sent_count = 0
    failed_count = 0

    for user_id in user_ids:
        try:
            await bot.send_message(
                user_id,
                formatted_text,
                parse_mode="HTML",
                # Важливо: не вимикайте прев'ю, якщо хочете бачити опис посилання
                disable_web_page_preview=False
            )
            sent_count += 1
        except TelegramForbiddenError:
            failed_count += 1
        except Exception as e:
            print(f"Не вдалося надіслати повідомлення користувачу {user_id}: {e}")
            failed_count += 1

    await message.answer(
        f"Розсилку завершено.\n\n✅ Надіслано: {sent_count}\n❌ Не вдалося надіслати: {failed_count}",
        reply_markup=get_admin_kb()
    )
    await state.clear()

@router.message(F.text == "Статистика")
async def get_statistics(message: types.Message):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    await message.answer(
        "Оберіть дію:",
        reply_markup=get_statistic_kb()
    )

@router.message(F.text == "Отримати всі команди")
async def show_all_teams(message: types.Message): # <--- Нова назва
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    # 3. Викликаємо правильну функцію
    teams_cursor = await get_all_teams()
    if not teams_cursor:
        await message.answer("Немає зареєстрованих команд.")
        return

    team_list = await teams_cursor.to_list(length=None)
    if not team_list:
        await message.answer("Немає зареєстрованих команд.")
        return

    response = "<b>Список всіх команд:</b>\n\n"
    for team in team_list:
        team_name = team.get("team_name", "Невідомо")
        team_id = team.get("team_id", "Невідомо")
        members = team.get("members", [])
        
        # Додаємо html.escape для безпечного відображення
        response += f"Команда: <b>{html.escape(str(team_name))}</b>\n"
        response += f"ID Команди: <b>{html.escape(str(team_id))}</b>\n"
        response += f"Кількість учасників: <b>{len(members)}</b>\n"
        response += "-----------------------\n"
    
    # Потрібно надіслати `response` користувачу
    await message.answer(response, parse_mode="HTML")