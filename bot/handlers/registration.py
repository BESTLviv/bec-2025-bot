from aiogram import Router, types, F
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import re
from bot.keyboards.registration import get_uni_kb, main_menu_kb, get_course_kb, where_kb, get_reg_kb
from bot.utils.database import save_user_data


router = Router()

class Registration(StatesGroup):
    name = State()
    age = State()
    course = State()
    university = State()
    speciality = State()
    expect_custom_uni = State()
    email = State()
    approval = State() 

def is_correct_text(text):
    text = text.strip()
    if not text:
        return False
    if len(text) > 30:
        return False
    return bool(re.search(r'[a-zA-Zа-яА-ЯіІїЇєЄґҐ]', text)) and not re.fullmatch(r'[\W_]+', text)

def is_correct_speciality(text):
    text = text.strip()
    if not text:
        return False
    if len(text) > 85:
        return False
    return bool(re.search(r'[a-zA-Zа-яА-ЯіІїЇєЄґҐ]', text)) and not re.fullmatch(r'[\W_]+', text)

def is_valid_age(text):
    return text.isdigit() and 16 <= int(text) <= 79

def is_valid_email(text):
    return bool(re.fullmatch(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text.strip()
    ))

@router.message(F.text == "Зареєструватися на змагання💡")
async def start_registration(message: types.Message, state: FSMContext):

    photo_path = "assets/register.png"
    photo_to_send = FSInputFile(photo_path)

    await message.answer_photo(
        photo=photo_to_send, 
        caption="Нумо знайомитись! Напиши своє ім'я та прізвище у форматі: Богдан Ковальчук",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.name)

@router.message(Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    name = message.text.strip()
    if not is_correct_text(name):
        await message.answer("🚫 Некоректне ім’я. Спробуй ще раз. Використовуй лише літери.")
        return

    parts = name.split()
    if len(parts) != 2:
        await message.answer("Напиши своє ім'я та прізвище у форматі: Богдан Ковальчук")
        return

    await state.update_data(name=name)
    data = await state.get_data()
    await message.answer(
        f"Приємно познайомитись, <b>{data['name'].split()[0]}!</b> Тепер напиши скільки тобі років!",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.age)

@router.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення")
        return
    age_text = message.text.strip()
    if not age_text.isdigit():
        await message.answer("Напиши правильний вік (числом)")
        return
    age_int = int(age_text)
    if age_int > 30:
        await message.answer("Хей невже ти такий старий? Напиши справжній вік")
        return
    elif age_int < 16:
        await message.answer("Хей невже ти такий малий? Напиши справжній вік")
        return

    await state.update_data(age=age_int)
    await message.answer(
        "Гарний вік! Тепер обери, на якому курсі ти навчаєшся😎",
        reply_markup=get_course_kb(),
        parse_mode="HTML"
    )
    await state.set_state(Registration.course)

@router.message(Registration.course)
async def ask_university_or_finish(message: types.Message, state: FSMContext):
    courses = ["1 курс", "2 курс", "3 курс", "4 курс", "Магістратура", "Інше", "Не навчаюсь"]

    if message.text not in courses:
        await message.answer("⚠️ Некоректні дані. Обери курс зі списку.")
        return
    
    if message.text == "Не навчаюсь":
        await message.answer(
            "На жаль, ми проводимо змагання лише для студентів університетів.",
            reply_markup=get_reg_kb()
        )
        await state.clear()
        return

    await state.update_data(course=message.text)
  
    await message.answer("Круто, а в якому навчальному закладі вчишся?", reply_markup=get_uni_kb())
    await state.set_state(Registration.university)

@router.message(Registration.university)
async def ask_speciality(message: types.Message, state: FSMContext):
    text = message.text.strip()
    unis = ["🎓 НУ “ЛП”", "🎓 ЛНУ ім. І. Франка", "🎓 УКУ", "🎓 Інший"]

    if message.text == "🎓 Інший":
        await message.answer("Вкажи назву свого навчального закладу:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(Registration.expect_custom_uni)
        return
    
    if message.text not in unis:
        await message.answer("⚠️ Некоректні дані. Обери університет зі списку.")
        return


    await state.update_data(university=text)

    await message.answer(
        "Супер, а на якій спеціальності свої роки проводиш? Напиши назву повністю, наприклад: Автоматизація, комп'ютерно інтегровані технології та робототехніка",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.speciality)

@router.message(Registration.expect_custom_uni)
async def process_custom_university(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    if not is_correct_text(text):
        await message.answer("⚠️ Некоректна назва університету. Спробуй ще раз.")
        return

    await state.update_data(university=text)

    await message.answer(
        "Супер, а на якій спеціальності свої роки проводиш?\nНапиши назву повністю, наприклад: Автоматизація, комп'ютерно інтегровані технології та робототехніка",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.speciality)

@router.message(Registration.speciality)
async def ask_where(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    if not is_correct_speciality(message.text):
        await message.answer("⚠️ Схоже, що дані введені неправильно. Спробуй ще раз. Використовуй лише літери.")
        return

    await state.update_data(speciality=message.text)
    await message.answer(
        "А електронною поштою поділишся?",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Registration.email)

@router.message(Registration.email)
async def ask_approval(message: types.Message, state: FSMContext):
    if message.text is None:
        await message.answer("🚫 Будь ласка, введи текстове повідомлення.")
        return
    text = message.text.strip()
    if not is_valid_email(text):
        await message.answer("⚠️ Схоже, що дані введені неправильно. Спробуй ще раз. у форматі example@mail.com")
        return
    await state.update_data(email=text)
    await message.answer(
        "Ну ось ми і познайомились🧡.\nТепер багато про тебе знаю. Даєш дозвіл для обробки персональної інформації?",
        parse_mode="HTML",
        reply_markup=where_kb()
    ) 
    await state.set_state(Registration.approval)

@router.message(Registration.approval)
async def process_approval(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    data = await state.get_data()
    # Лічильник відмов
    deny_count = data.get("deny_count", 0)

    if text == "так":
        await save_user_data(
            user_id=message.from_user.id,
            user_name=message.from_user.username,
            name=data["name"],
            age=data["age"],
            course=data["course"],
            university=data["university"],
            speciality=data["speciality"],
            email=data["email"],
            team='-'
        )
        await message.answer(
            "✅ Ви успішно зареєструвалися в Telegram-боті.\nЩоб взяти участь у змаганнях і бути допущеним до тестового завдання, вам потрібно зібрати команду з 4 людей.\n\nДолучайтесь до чату учасників, щоб знайти команду або поставити питання:<a href='https://t.me/+EqpOjlPkgRtjYmEy'> Приєднатися</a>",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
        await state.clear()
    elif text == "ні":
        deny_count += 1
        await state.update_data(deny_count=deny_count)
        if deny_count >= 2:
            await message.answer(
                "Ти двічі відмовився від згоди. Повертаємо до меню реєстрації.",
                parse_mode="HTML",
                reply_markup=get_reg_kb()
            )
            await state.clear()
        else:
            await message.answer(
                "Для закінчення реєстрації нам потрібна ця згода",
                parse_mode="HTML",
                reply_markup=where_kb()
            )
    else:
        await message.answer(
            "Будь ласка, обери <b>Так</b> або <b>Ні</b>.",
            parse_mode="HTML",
            reply_markup=where_kb()
        )
