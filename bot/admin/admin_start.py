import os
import re
import html
from aiogram import F, Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError
from dotenv import load_dotenv
import asyncio

# Переконайтесь, що всі імпорти правильні та відповідають вашому проєкту
from bot.admin.admin_keyboard import get_admin_kb
from bot.utils.database import get_all_teams, get_all_user_ids, get_all_users_with_cv, get_no_team_user_ids

load_dotenv()
router = Router()

# --- FSM Стани ---
class SpamStates(StatesGroup):
  choosing_audience = State()
  waiting_for_message = State()

# --- ОБРОБНИК ГОЛОВНОГО МЕНЮ АДМІНА ---
@router.message(F.text == os.getenv("ADMIN_START"))
async def admin_start(message: types.Message):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id == admin_id:
        await message.answer(
            "Привіт, Адміністраторе!",
            reply_markup=get_admin_kb(),
            parse_mode="HTML"
        )
    return

# 1. СТАРТ РОЗСИЛКИ: ВИБІР АУДИТОРІЇ
@router.message(F.text == "Розсилка")
async def start_spam(message: types.Message, state: FSMContext):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Всім користувачам", callback_data="spam_to_all")],
        [InlineKeyboardButton(text="Користувачам без команди", callback_data="spam_to_no_team")],
        [InlineKeyboardButton(text="❌ Скасувати", callback_data="spam_cancel")]
    ])
    await message.answer("Оберіть аудиторію для розсилки:", reply_markup=keyboard)
    await state.set_state(SpamStates.choosing_audience)

# 2. ОБРОБКА ВИБОРУ АУДИТОРІЇ
@router.callback_query(SpamStates.choosing_audience, F.data.startswith("spam_to_"))
async def choose_audience(callback: types.CallbackQuery, state: FSMContext):
    audience = callback.data.split("_")[-1]
    await state.update_data(audience=audience)
    await callback.message.edit_text("Тепер введіть текст розсилки або 'Назад' для відміни:")
    await state.set_state(SpamStates.waiting_for_message)
    await callback.answer()

# 3. ФІНАЛЬНИЙ КРОК: ВІДПРАВКА РОЗСИЛКИ
@router.message(SpamStates.waiting_for_message)
async def send_spam(message: types.Message, state: FSMContext, bot: Bot):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    if message.text.lower() == "назад":
        await message.answer("Розсилку скасовано.", reply_markup=get_admin_kb())
        await state.clear()
        return

    user_data = await state.get_data()
    audience = user_data.get("audience")

    if audience == "all":
        user_ids = await get_all_user_ids()
        audience_name = "всім користувачам"
    elif audience == "no_team":
        user_ids = await get_no_team_user_ids()
        audience_name = "користувачам без команди"
    else:
        await message.answer("Помилка: невідома аудиторія. Розсилку скасовано.", reply_markup=get_admin_kb())
        await state.clear()
        return

    raw_text = message.text or ""

    url_regex = re.compile(r'https?://t\.me/[^\s)]+')
    matches = list(url_regex.finditer(raw_text))
    if matches:
        first_match = matches[0]
        url = first_match.group(0)
        before_text = html.escape(raw_text[:first_match.start()])
        after_text = html.escape(raw_text[first_match.end():])
        formatted_text = f'{before_text}<a href="{url}">Приєднатися</a>{after_text}'
    else:
        formatted_text = html.escape(raw_text)
    
    await message.answer(f"⏳ Починаю розсилку для '{audience_name}' ({len(user_ids)} користувачів)...")

    sent_count, failed_count = 0, 0
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, formatted_text, parse_mode="HTML", disable_web_page_preview=False)
            sent_count += 1
            # Додаємо невелику затримку для уникнення блокування
            await asyncio.sleep(0.1)
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

# 4. ОБРОБНИК СКАСУВАННЯ
@router.callback_query(SpamStates.choosing_audience, F.data == "spam_cancel")
async def cancel_spam(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Розсилку скасовано.")
    await callback.message.answer("Головне меню:", reply_markup=get_admin_kb())


# --- ІНШІ ФУНКЦІЇ АДМІНА ---

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

    await message.answer(f"Знайдено {len(users)} резюме. Починаю відправку...")
    for user in users:
        file_id = user.get("cv_file_path")
        username = user.get("username", "невідомо")
        user_id = user.get("telegram_id", "null")

        if file_id:
            try:
                await message.answer_document(
                    document=file_id,
                    caption=f"Користувач: @{username}\nID: `{user_id}`",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Помилка відправки CV від {username}: {e}")
    await message.answer("✅ Всі наявні CV надіслано.")

@router.message(F.text == "Отримати всі команди")
async def show_all_teams(message: types.Message):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    teams_cursor = await get_all_teams()
    team_list = await teams_cursor.to_list(length=None)

    if not team_list:
        await message.answer("Немає зареєстрованих команд.")
        return

    response = "<b>Список всіх команд:</b>\n\n"
    for team in team_list:
        team_name = team.get("team_name", "Невідомо")
        team_id = team.get("team_id", "Невідомо")
        members = team.get("members", [])
        
        response += f"Команда: <b>{html.escape(str(team_name))}</b>\n"
        response += f"ID Команди: <code>{html.escape(str(team_id))}</code>\n"
        response += f"Кількість учасників: <b>{len(members)}</b>\n"
        response += "-----------------------\n"
    
    await message.answer(response, parse_mode="HTML")