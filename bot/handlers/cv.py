from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile

# Припускаємо, що ці імпорти у вас вже є і вони коректні
from bot.keyboards.cv_keyboard import get_back_cv_kb, get_cv_kb
from bot.keyboards.registration import main_menu_kb
from bot.utils.cv_db import update_cv_file_path, add_cv
from bot.utils.database import users_collection

router = Router()

# 1. Створюємо стани для процесу завантаження CV
class CVStates(StatesGroup):
    waiting_for_cv_file = State()

@router.message(F.text == "CV📜")
async def cv_start(message: types.Message, state: FSMContext):
    await state.clear() # Очищуємо попередній стан, якщо він був
    user_id = message.from_user.id
    user_data = await users_collection.find_one({"telegram_id": user_id})

    caption_text = ""
    if user_data and user_data.get("cv_file_path"):
        caption_text = "Ви вже відправили CV, хочете надіслати нове?"
    else:
        caption_text = "У цьому меню ти зможеш відправити CV! Воно може зацікавити роботодавців і змінити твоє життя🤩"

    await message.answer_photo(
        photo=FSInputFile("assets/cv.png"),
        caption=caption_text,
        parse_mode="HTML",
        reply_markup=get_cv_kb()
    )

@router.message(F.text == "Назад до меню🔙")
async def back_to_main_menu_from_cv(message: types.Message, state: FSMContext):
    await state.clear() # Важливо очистити стан при виході в головне меню
    await message.answer(
        "Ви повернулись назад до меню",  
        reply_markup=main_menu_kb()
    )

@router.message(F.text == "📤 Надіслати готове CV")
async def cv_prompt_send(message: types.Message, state: FSMContext):   
    await message.answer(
        "Будь ласка, надішли своє CV у форматі PDF або DOCX.",
        reply_markup=get_back_cv_kb()
    )
    # 2. Ставимо користувача у стан очікування файлу
    await state.set_state(CVStates.waiting_for_cv_file)

# 5. Перейменовуємо функції, щоб уникнути конфлікту імен. 
# Ця кнопка "Назад" веде з меню відправки файлу назад до меню CV.
@router.message(F.text == "Назад🔙")
async def back_to_cv_menu(message: types.Message, state: FSMContext):
    await state.clear() # Виходимо зі стану очікування файлу
    await message.answer(
        "Ви повернулися назад до меню CV.",
        reply_markup=get_cv_kb()
    )

# 3. Цей обробник тепер реагує ТІЛЬКИ у стані waiting_for_cv_file
@router.message(CVStates.waiting_for_cv_file, F.document)
async def handle_cv_file(message: types.Message, state: FSMContext):
    if not message.document: # Додаткова перевірка
        return

    file_name = message.document.file_name or ""
    mime_type = (message.document.mime_type or "").lower()
    
    # Дозволені типи файлів
    allowed_mime_types = [
        "application/pdf", 
        "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    allowed_extensions = [".pdf", ".doc", ".docx"]

    is_allowed = (mime_type in allowed_mime_types) or any(file_name.lower().endswith(ext) for ext in allowed_extensions)

    if not is_allowed:
        await message.answer("❗ Упс, дозволені тільки формати PDF, DOC, DOCX. Спробуй ще раз.")
        return # Залишаємо користувача в стані очікування файлу

    max_file_size = 10 * 1024 * 1024  # 10 МБ
    if message.document.file_size > max_file_size:
        await message.answer("Упс. Схоже, файл завеликий. Його розмір має бути не більшим за 10 МБ.")
        return
    
    file_id = message.document.file_id
    user_id = message.from_user.id

    # Зберігаємо file_id в базі даних
    await update_cv_file_path(user_id, file_id)
    # Ця функція, ймовірно, робить те саме, що й попередня. Можливо, одна з них зайва.
    # Якщо вони виконують різні дії, залиште обидві.
    await add_cv(user_id=user_id, cv_file_id=file_id)
    
    await message.answer("✅ CV завантажено! 🎉", reply_markup=main_menu_kb())
    
    # 4. Очищуємо стан після успішного завантаження
    await state.clear()

# Обробник для будь-якого іншого тексту в стані очікування файлу
@router.message(CVStates.waiting_for_cv_file, F.text)
async def handle_wrong_input_in_cv_state(message: types.Message):
    await message.answer("Будь ласка, надішліть саме файл (PDF, DOCX) або натисніть кнопку 'Назад🔙'.")


# @router.message(F.text == "Перевірити своє CV")
# async def cv_check(message: types.Message):
#     user_id = message.from_user.id
#     user_data = await users_collection.find_one({"telegram_id": user_id})

#     if user_data and user_data.get("cv_file_path"):
#         await message.answer("Знайшов твоє CV, зараз надішлю...")
#         cv_file_id = user_data.get("cv_file_path")
#         await message.answer_document(
#             document=cv_file_id,
#             caption="Ось твоє CV. Якщо хочеш надіслати нове, обери '📤 Надіслати готове CV'.",
#             reply_markup=get_cv_kb()
#         )
#     else:
#         await message.answer(
#             "Упс, здається, ти ще не надіслав жодного CV.",
#             reply_markup=get_cv_kb()
#         )

@router.message(F.text == "Перевірити своє CV")
async def cv_check(message: types.Message):
    user_id = message.from_user.id
    user_data = await users_collection.find_one({"telegram_id": user_id})

    if user_data and user_data.get("cv_file_path"):
        cv_file_id = user_data.get("cv_file_path")
        
        # Об'єднуємо текст та відправку документа в одне повідомлення
        try:
            await message.answer_document(
                document=cv_file_id,
                caption="Знайшов твоє CV! Ось воно.\n\nЯкщо хочеш надіслати нове, обери '📤 Надіслати готове CV'.",
                reply_markup=get_cv_kb()
            )
        except Exception as e:
            # Якщо виникне помилка при відправці, повідомимо користувача
            print(f"Помилка при відправці CV для user_id {user_id}: {e}") # Це буде видно у вашій консолі
            await message.answer(
                "Упс, не вдалося надіслати твоє CV. Можливо, файл пошкоджено. Спробуй завантажити його знову.",
                reply_markup=get_cv_kb()
            )
    else:
        await message.answer(
            "Упс, здається, ти ще не надіслав жодного CV.",
            reply_markup=get_cv_kb()
        )