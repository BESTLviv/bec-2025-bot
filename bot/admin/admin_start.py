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
from bot.admin.admin_keyboard import get_admin_kb, get_statistic_kb
from bot.utils.database import get_all_teams, get_all_user_ids, get_all_users_with_cv, get_all_td_teams, get_all_id_teams, users_collection, get_user_ids_by_category, get_all_participants_info

load_dotenv()
router = Router()

# --- FSM Стани ---
class SpamStates(StatesGroup):
  choosing_audience = State()
  waiting_for_message = State()

class CategorySpamStates(StatesGroup):
    waiting_for_pdf = State()
    waiting_for_caption = State()

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
        # Define the function to fetch user IDs without a team
        async def get_no_team_user_ids():
            users_cursor = await users_collection.find({"team_id": None}).to_list(length=None)
            return [user["telegram_id"] for user in users_cursor if "telegram_id" in user]

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
async def show_all_teams(message: types.Message):
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

@router.message(F.text == "Отримати всі не повні команди")
async def show_all_incomplete_teams(message: types.Message): 
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    teams_cursor = await get_all_teams()
    team_list = await teams_cursor.to_list(length=None)

    if not team_list:
        await message.answer("Немає зареєстрованих команд.")
        return

    incomplete_teams = [team for team in team_list if len(team.get("members", [])) < 4]

    if not incomplete_teams:
        await message.answer("Всі команди повні.")
        return

    response = "<b>Список неповних команд:</b>\n\n"
    for team in incomplete_teams:
        team_name = team.get("team_name", "Невідомо")
        team_id = team.get("team_id", "Невідомо")
        cat = team.get("category", "Невідомо")
        member_ids = team.get("members", []) # Це список ObjectId
        
        response += f"Команда: <b>{html.escape(str(team_name))}</b>\n"
        response += f"ID Команди: <code>{html.escape(str(team_id))}</code>\n"
        response += f"Категорія: <code>{html.escape(str(cat))}</code>\n"
        response += f"Кількість учасників: <b>{len(member_ids)}</b>/{4}\n"
        
        if member_ids:
            response += "Учасники:\n"
            
            # --- ОСНОВНА ЗМІНА ТУТ ---
            # Робимо один запит до БД, щоб отримати всі документи користувачів,
            # чиї ID знаходяться в списку member_ids.
            member_docs = await users_collection.find(
                {"_id": {"$in": member_ids}}
            ).to_list(length=None)
            # --- КІНЕЦЬ ЗМІНИ ---

            # Тепер ітеруємо по отриманих документах-словниках
            for member_doc in member_docs:
                # Цей рядок тепер працюватиме, бо member_doc - це словник
                username = member_doc.get("username", "Невідомо")
                response += f" - @{html.escape(str(username))}\n"
        
        response += "-----------------------\n"
    
    await message.answer(response, parse_mode="HTML")


@router.message(F.text == "Отримати всі ID")
async def get_all_ids(message: types.Message): 
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    teams_cursor = await get_all_id_teams()
    team_list = await teams_cursor.to_list(length=None)

    if not team_list:
        await message.answer("Немає зареєстрованих команд.")
        return
    team_len = len(team_list)
    response = f"<b>Список всіх ID команд:</b>\nКількість: {team_len}\n"
    for team in team_list:
        team_id = team.get("team_id", "Невідомо")
        member_ids = team.get("members", []) # Це список ObjectId
        response += f"Команда: <b>{html.escape(str(team['team_name']))}</b>\n"
        response += f"ID Команди: <code>{html.escape(str(team_id))}</code>\n"
        response += f"Кількість учасників: <b>{len(member_ids)}</b>/{4}\n"

    await message.answer(response, parse_mode="HTML")


@router.message(F.text == "Отримати всі TD")
async def get_all_td(message: types.Message): 
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    teams_cursor = await get_all_td_teams()
    team_list = await teams_cursor.to_list(length=None)

    if not team_list:
        await message.answer("Немає зареєстрованих команд.")
        return
    team_len = len(team_list)
    response = f"<b>Список всіх TD команд:</b>\nКількість: {team_len}\n"
    for team in team_list:
        team_id = team.get("team_id", "Невідомо")
        member_ids = team.get("members", []) # Це список ObjectId
        response += f"Команда: <b>{html.escape(str(team['team_name']))}</b>\n"
        response += f"ID Команди: <code>{html.escape(str(team_id))}</code>\n"
        response += f"Кількість учасників: <b>{len(member_ids)}</b>/{4}\n"

    await message.answer(response, parse_mode="HTML")

# 1. СТАРТ РОЗСИЛКИ ДЛЯ TEAM DESIGN
@router.message(F.text == "Розсилка по TD")
async def start_td_spam(message: types.Message, state: FSMContext):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return
    
    await state.set_state(CategorySpamStates.waiting_for_pdf)
    await state.update_data(category="Team Design")
    await message.answer(
        "Ви обрали розсилку для команд 'Team Design'.\n"
        "Будь ласка, надішліть PDF-файл.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# 2. СТАРТ РОЗСИЛКИ ДЛЯ INNOVATIVE DESIGN
@router.message(F.text == "Розсилка по ID")
async def start_id_spam(message: types.Message, state: FSMContext):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return
    
    await state.set_state(CategorySpamStates.waiting_for_pdf)
    await state.update_data(category="Innovative Design")
    await message.answer(
        "Ви обрали розсилку для команд 'Innovative Design'.\n"
        "Будь ласка, надішліть PDF-файл.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# 3. ОБРОБКА ОТРИМАНОГО PDF-ФАЙЛУ
@router.message(CategorySpamStates.waiting_for_pdf, F.document)
async def process_spam_pdf(message: types.Message, state: FSMContext):

    pdf_file_id = message.document.file_id
    await state.update_data(pdf_file_id=pdf_file_id)
    await state.set_state(CategorySpamStates.waiting_for_caption)
    await message.answer("✅ Файл отримано. Тепер надішліть текст (опис) до файлу.")

@router.message(CategorySpamStates.waiting_for_pdf)
async def wrong_pdf_input(message: types.Message):
    await message.answer("Помилка. Будь ласка, надішліть саме PDF-файл.")

# 4. ОБРОБКА ТЕКСТУ ТА ФІНАЛЬНА ВІДПРАВКА
@router.message(CategorySpamStates.waiting_for_caption)
async def process_caption_and_send(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    category = data.get("category")
    pdf_file_id = data.get("pdf_file_id")
    caption = message.text

    if not category or not pdf_file_id:
        await message.answer("Сталася помилка, не знайдено категорію або файл. Спробуйте знову.", reply_markup=get_admin_kb())
        await state.clear()
        return

    user_ids = await get_user_ids_by_category(category)

    if not user_ids:
        await message.answer(f"Не знайдено користувачів у категорії '{category}'. Розсилку скасовано.", reply_markup=get_admin_kb())
        await state.clear()
        return

    await message.answer(f"⏳ Починаю розсилку для '{category}' ({len(user_ids)} користувачів)...")
    
    sent_count, failed_count = 0, 0
    for user_id in user_ids:
        try:
            await bot.send_document(
                chat_id=user_id,
                document=pdf_file_id,
                caption=caption,
                parse_mode="HTML" # Можете додати, якщо хочете форматувати опис
            )
            sent_count += 1
            await asyncio.sleep(0.1)  # Затримка для уникнення блокування
        except TelegramForbiddenError:
            failed_count += 1
        except Exception as e:
            print(f"Не вдалося надіслати повідомлення користувачу {user_id}: {e}")
            failed_count += 1

    await message.answer(
        f"Розсилку для '{category}' завершено.\n\n"
        f"✅ Надіслано: {sent_count}\n"
        f"❌ Не вдалося надіслати: {failed_count}",
        reply_markup=get_admin_kb()
    )
    await state.clear()
@router.message(F.text == "Отримати інформацію учасників")
async def get_participant_info(message: types.Message):
    admin_id = int(os.getenv("ADMIN_ID"))
    if message.from_user.id != admin_id:
        return

    participants = await get_all_participants_info()

    if not participants:
        await message.answer("Не знайдено жодного учасника в командах, позначених як 'is_participant: true'.")
        return

    # Ініціалізація словників та змінних для статистики
    university_stats = {
        "НУ “ЛП”": 0, "ЛНУ ім. І. Франка": 0, "УКУ": 0, "Інший": 0
    }
    course_stats = {
        "1 курс": 0, "2 курс": 0, "3 курс": 0, "4 курс": 0,
        "Магістратура": 0, "Не навчаюсь": 0, "Інше": 0
    }
    total_age = 0
    valid_age_count = 0
    
    full_response = ""
    for user in participants:
        # Отримуємо дані для статистики
        university = user.get("university")
        course = user.get("course")
        age = user.get("age") # Використовуємо 'age'

        # Підрахунок статистики
        if university in university_stats:
            university_stats[university] += 1
        
        if course in course_stats:
            course_stats[course] += 1

        total_age += int(age)
        valid_age_count += 1

        # Формування відповіді з інформацією про користувача
        name = html.escape(user.get("name", "Не вказано"))
        username = html.escape(user.get("username", "Не вказано"))
        user_university = html.escape(university or "Не вказано")
        speciality = html.escape(user.get("speciality", "Не вказано"))
        user_course = html.escape(course or "Не вказано")

        user_block = (
            f"👤 <b>Ім'я:</b> {name}\n"
            f"✈️ <b>Username:</b> @{username}\n"
            f"🏛 <b>Університет:</b> {user_university}\n"
            f"🔬 <b>Спеціальність:</b> {speciality}\n"
            f"🎓 <b>Курс:</b> {user_course}\n"
            "-----------------------\n"
        )
        full_response += user_block

    # Розрахунок середнього віку
    average_age = total_age / valid_age_count if valid_age_count > 0 else 0

    # Формування блоку зі статистикою
    stats_summary = "<b>📊 Статистика Учасників:</b>\n\n"
    stats_summary += "<b>🎓 По Університетах:</b>\n"
    for uni, count in university_stats.items():
        stats_summary += f"- {uni}: <b>{count}</b>\n"
    
    stats_summary += "\n<b>📈 По Курсах:</b>\n"
    for course_name, count in course_stats.items():
        stats_summary += f"- {course_name}: <b>{count}</b>\n"
        
    stats_summary += f"\n<b>🎂 Середній вік:</b> <b>{average_age:.1f} років</b>\n"
    stats_summary += "-----------------------\n\n"

    # Загальний заголовок та комбінація повідомлення
    response_header = f"<b>✅ Знайдено інформацію про {len(participants)} учасників.</b>\n\n"
    final_message = response_header + stats_summary + "<b>📝 Список учасників:</b>\n\n" + full_response

    # Відправка повідомлення (з розбиттям, якщо воно занадто довге)
    if len(final_message) > 4096:
        await message.answer(response_header + stats_summary, parse_mode="HTML")
        await asyncio.sleep(0.5)
        
        for i in range(0, len(full_response), 4096):
            chunk = full_response[i:i + 4096]
            await message.answer(chunk, parse_mode="HTML")
            await asyncio.sleep(0.5) 
    else:
        await message.answer(final_message, parse_mode="HTML")
