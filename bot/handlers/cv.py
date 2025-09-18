from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from bot.keyboards.cv_keyboard import get_back_cv_kb, get_cv_kb
from bot.handlers.registration import is_correct_text
from bot.keyboards.registration import main_menu_kb
from bot.utils.cv_db import update_cv_file_path, add_cv
from bot.keyboards.team import get_have_team_kb
from bot.utils.database import is_user_have_cv, is_user_in_team, users_collection
from aiogram.types import FSInputFile

router = Router()


@router.message(F.text == "CV📜")
async def cv_start(message: types.Message):
    user_id = message.from_user.id
    user_data = await users_collection.find_one({"telegram_id": user_id})
    if user_data and user_data.get("cv_file_path") is not None:
        await message.answer_photo(
            photo=FSInputFile("assets/cv.png"),
            caption="Ви вже відправили CV, хочете ще раз відправити?",
            parse_mode="HTML",
            reply_markup=get_cv_kb()
        )
    else:
        await message.answer_photo(
            photo=FSInputFile("assets/cv.png"),
            caption="У цьому меню ти зможеш відправити CV! Воно може зацікавити роботодавців і змінити твоє життя🤩",
            parse_mode="HTML",
            reply_markup=get_cv_kb()
        )

@router.message(F.text == "Назад до меню🔙")
async def cv_back(message: types.Message, state: FSMContext):
    await message.answer(
        "Ви повернулись назад до меню",  
        reply_markup=main_menu_kb()
    )

@router.message(F.text == "📤 Надіслати готове CV")
async def cv_send(message: types.Message, state: FSMContext):   
    if not is_correct_text(message.text):
        await message.answer(
            "⚠️ Схоже, що дані введені неправильно. Будь ласка, спробуй ще раз!"
        )
        return
    await message.answer(
        "Будь ласка, надішли своє CV у форматі PDF, DOCX.",
        reply_markup=get_back_cv_kb()
    )

@router.message(F.text == "Назад🔙")
async def cv_back(message: types.Message, state: FSMContext):
    await message.answer(
        "Ви повернулися назад до меню CV.",
        reply_markup=get_cv_kb()
    )


@router.message(F.document)
async def handle_cv_file(message: types.Message):
    file_name = message.document.file_name or ""
    mime_type = (message.document.mime_type or "").lower()
    allowed_mime_types = ["application/pdf", "application/msword"]
    allowed_extensions = [".pdf", ".doc", ".docx"]

    if (mime_type not in allowed_mime_types) and not any(file_name.lower().endswith(ext) for ext in allowed_extensions):
        await message.answer("❗ Упс, дозволені тільки формати PDF, DOCX. Спробуй ще раз і надішли файл у відповідному форматі.")
        return

    max_file_size = 10 * 1024 * 1024  # 10 МБ
    if message.document.file_size > max_file_size:
        await message.answer("Упс. Схоже, файл завеликий. Його розмір має бути не більшим за 10 МБ.")
        return
    
    try:
        file_id = message.document.file_id
        file = await message.bot.get_file(file_id)
        if not file.file_path:
            await message.answer("❗ Помилка: не вдалося отримати шлях до файлу. Спробуй ще раз.")
            return
        print(f"File ID: {file_id}, File Path: {file.file_path}")
        await message.bot.download_file(file.file_path, timeout=30)
    except Exception:
        await message.answer("🕒 Файл завантажується дуже довго… Перевір розмір і спробуй ще раз!")
        return
    
    user_id = message.from_user.id
    await update_cv_file_path(user_id, file_id)
    await add_cv(user_id=user_id, cv_file_id=file_id)
    await message.answer("✅ CV завантажено! 🎉", reply_markup=main_menu_kb())


@router.message(F.text == "Перевірити своє CV")
async def cv_check(message: types.Message):
    user_id = message.from_user.id
    user_data = await users_collection.find_one({"telegram_id": user_id})

    if user_data and user_data["cv_file_path"] not in [None, "null"]:
        
        await message.answer("Знайшов твої CV, зараз надішлю...")

        cv_file_id = user_data.get("cv_file_path")

        if cv_file_id:
            await message.answer_document(
            document=cv_file_id,
            caption="Ось твоє CV. Якщо хочеш надіслати нове, обери '📤 Надіслати готове CV'.",
            reply_markup=get_cv_kb()
            )
        else:
            print(f"Warning: CV entry for user {user_id} is missing file_id.")

    else:
        await message.answer(
            "Упс, здається, ти ще не надіслав жодного CV. Будь ласка, надішли його у форматі PDF або DOCX.",
            reply_markup=get_cv_kb()
        )
