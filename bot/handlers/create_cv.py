from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.cv_keyboard import get_back_kb, get_is_correct_kb
from bot.keyboards.registration import main_menu_kb
from bot.handlers.registration import is_correct_text
from bot.utils.database import get_user
from bot.utils.cv_db import add_cv
import re
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from aiogram.types import BufferedInputFile
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("DejaVuSans", "assets/fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "assets/fonts/DejaVuSans-Bold.ttf"))


router = Router()

class CVStates(StatesGroup):
    position = State()
    languages = State()
    education = State()

    speciality = State()
    skills = State()
    experience = State()
    contacts = State()
    about = State()
    confirm = State()

@router.message(F.text == "Створити CV")
async def cv_start(message: types.Message, state: FSMContext):
    if not is_correct_text(message.text):
        await message.answer("Введіть коректний текст для")
        return
    await message.answer(
        "Тож почнімо, яка посада або напрям тебе цікавить?",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.position)

@router.message(CVStates.position)
async def process_position_input(message: types.Message, state: FSMContext):
    if not is_correct_text(message.text):
        await message.answer("Введіть коректний текст для")
        return
    await state.update_data(position=message.text)
    await message.answer(
        "Якими мовами ти володієш. Вкажи рівень володіння. Наприклад: українська — рідна, англійська — B2.",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.languages)

@router.message(CVStates.languages)
async def process_languages_input(message: types.Message, state: FSMContext):
    # You may need to import these from your menu module
    
    if not is_correct_text(message.text):
        await message.answer("⚠️ Схоже, що дані введені неправильно. Спробуй ще раз!")
        return

    VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2", "А1", "А2", "В1", "В2", "С1", "С2"}
    text = message.text.lower()
    all_levels_raw = re.findall(r'\b([a-zA-ZА-Яа-я][0-9])\b', message.text)
    all_levels_upper = [level.upper() for level in all_levels_raw]
    has_native = "рідна" in text
    valid_levels = [level for level in all_levels_upper if level in VALID_LEVELS]
    invalid_levels = [level for level in all_levels_upper if level not in VALID_LEVELS]

    if not has_native and not all_levels_raw:
        await message.answer("⚠️ Вкажи рівень володіння. Наприклад: українська — рідна, англійська — B2.")
        return
    if invalid_levels or (not has_native and not valid_levels):
        await message.answer("⚠️ Неправильний формат рівня. Спробуй ще раз!")
        return

    await state.update_data(languages=message.text)
    await message.answer(
        "Напиши в якому університеті ти вчишся",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.education)

@router.message(CVStates.education)
async def process_education_input(message: types.Message, state: FSMContext):
    await state.update_data(education=message.text)
    await message.answer(
        "На якій спеціальності вчишся? Також згадай про курси, які проходив!",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.speciality)

@router.message(CVStates.speciality)
async def process_speciality_input(message: types.Message, state: FSMContext):
    await state.update_data(speciality=message.text)
    await message.answer(
        "Розкажи про свої Hard і Soft skills",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.skills)

@router.message(CVStates.skills)
async def process_skills_input(message: types.Message, state: FSMContext):
    await state.update_data(skills=message.text)
    await message.answer(
        "Чи працював вже десь? Обов'язково напиши про це! Якщо ще не маєш досвіду роботи напиши 'НІ'",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.experience)

@router.message(CVStates.experience)
async def process_experience_input(message: types.Message, state: FSMContext):
    await state.update_data(experience=message.text)
    await message.answer(
        "Тепер розкажи трохи про себе!",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.about)

@router.message(CVStates.about)
async def process_about_input(message: types.Message, state: FSMContext):
    await state.update_data(about=message.text)
    await message.answer(
        "Супер, залиш контактик: номер телефону та електронну пошту. За бажанням, можеш додати лінкедин.",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.contacts)

@router.message(CVStates.contacts)
async def process_contacts_input(message: types.Message, state: FSMContext):
    await state.update_data(contacts=message.text)
    await message.answer(
        "Чи все правильно?",
        parse_mode="HTML",
        reply_markup=get_is_correct_kb()
    )
    await state.set_state(CVStates.confirm)

@router.message(F.text == "Ні")
async def process_confirm_no(message: types.Message, state: FSMContext):
    await message.answer(
        "Давайте спробуємо ще раз! Яка посада або напрям тебе цікавить?",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.clear()
    await state.set_state(CVStates.position)

def draw_sidebar(canvas, doc):
    """Малює прямокутник зліва на всю висоту"""
    canvas.saveState()
    width, height = letter  # розмір сторінки
    sidebar_width = 80      # ширина бокової панелі в пунктах

    # малюємо прямокутник (x=0, y=0, ширина, висота)
    canvas.setFillColor(colors.HexColor("#F5A020"))  # наприклад темно-сірий
    canvas.rect(0, 0, sidebar_width, height, stroke=0, fill=1)

    canvas.restoreState()

@router.message(F.text == "Так")
async def process_confirm_yes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        # Отримуємо ім'я користувача з бази даних або генеруємо за замовчуванням
        user = await get_user(message.from_user.id)
        user_name = user.get("name", f"user_{message.from_user.id}") if user else f"user_{message.from_user.id}"
        name_parts = user_name.split()
        user_name_safe = "_".join(name_parts) if name_parts else f"user_{message.from_user.id}"

        # Шлях для тимчасового збереження PDF
        pdf_path = f"cv_{user_name_safe}.pdf"

        # Створюємо PDF документ
        doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor="#F5A020",
            spaceAfter=18,
            alignment=1,
            fontName="DejaVuSans-Bold"   # ✅ заміна
        )
        # Стиль для підзаголовків (пункти CV)
        heading_style = ParagraphStyle(
            'HeadingStyle',
            parent=styles['Heading2'],
            fontSize=16,
            textColor="#000000",
            spaceAfter=10,
            fontName="DejaVuSans-Bold"   # ✅ заміна
        )

        body_style = ParagraphStyle(
            'BodyStyle',
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            spaceAfter=8,
            fontName="DejaVuSans"        # ✅ заміна
        )

        # Додаємо ім'я як заголовок
        story.append(Paragraph(user_name, title_style))
        story.append(Spacer(1, 0.3 * inch))

        # Додаємо всі пункти CV
        fields = [
            ("Бажана посада", data.get("position", "Не вказано")),
            ("Володіння мовами", data.get("languages", "Не вказано")),
            ("Освіта", data.get("education", "Не вказано")),
            ("Спеціальність", data.get("speciality", "Не вказано")),
            ("Досвід роботи", data.get("experience", "Не вказано")),
            ("Навички", data.get("skills", "Не вказано")),
            ("Про кандидата", data.get("about", "Не вказано")),
            ("Контакти", data.get("contacts", "Не вказано"))
        ]

        for label, content in fields:
            story.append(Paragraph(label, heading_style))
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 0.1 * inch))

        # Прибрано дату створення

        # Генеруємо PDF
        doc.build(story)

        # Читання PDF і підготовка до відправлення
        with open(pdf_path, "rb") as pdf_file:
            file_bytes = pdf_file.read()
            document = BufferedInputFile(file=file_bytes, filename=f"CV_{user_name_safe}.pdf")
            sent_doc = await message.answer_document(document)

        # Зберігаємо дані в базу з file_id
        await add_cv(
            user_id=message.from_user.id,
            position=data.get("position"),
            languages=data.get("languages"),
            education=data.get("education"),
            experience=data.get("experience"),
            skills=data.get("skills"),
            contacts=data.get("contacts"),
            about=data.get("about"),
            cv_file_id=sent_doc.document.file_id
        )

        await message.answer(
            "✅ Ваше CV успішно створено! Файл доступний для завантаження вище.",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
    except Exception as e:
        print(f"Exception occurred: {e}")
        await message.answer("❗ Сталася помилка під час створення або відправлення PDF. Спробуй ще раз пізніше.")
        return
    finally:
        # Видаляємо тимчасовий файл
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    await state.clear()