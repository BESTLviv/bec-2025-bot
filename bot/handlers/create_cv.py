import asyncio
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from bot.keyboards.cv_keyboard import get_back_kb, get_is_correct_kb
from bot.keyboards.registration import main_menu_kb
from bot.handlers.registration import is_correct_text
from bot.utils.database import get_user
from io import BytesIO
from aiogram.types import BufferedInputFile
from bot.utils.cv_db import add_cv
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Frame, PageTemplate, FrameBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("DejaVuSans", "assets/fonts/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "assets/fonts/DejaVuSans-Bold.ttf"))


router = Router()

class CVStates(StatesGroup):
    photo = State()
    position = State()
    languages = State()
    education = State()
    speciality = State()
    skills = State()
    experience = State()
    contacts = State()
    about = State()
    birthdate = State()
    confirm = State()


@router.message(F.text == "Створити CV")
async def cv_start(message: types.Message, state: FSMContext):
    if not is_correct_text(message.text):
        await message.answer("Введіть коректний текст")
        return
    await message.answer(
        "Тож почнімо, надішліть фото для твого CV",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.photo)
    
@router.message(CVStates.photo, F.photo)
async def process_photo_input(message: types.Message, state: FSMContext):
    photo = message.photo[-1]
    await state.update_data(photo=photo.file_id)

    await message.answer(
        "Яка посада або напрям тебе цікавить?",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.position)

@router.message(CVStates.position)
async def process_position_input(message: types.Message, state: FSMContext):
    if not is_correct_text(message.text):
        await message.answer("Введіть коректний текст")
        return
    await state.update_data(position=message.text)
    await message.answer(
        "Введи дату народження у форматі ДД.ММ.РРРР",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.birthdate)
    
@router.message(CVStates.birthdate)
async def process_birthdate_input(message: types.Message, state: FSMContext):
    birthdate_pattern = r'^(\d{2})\.(\d{2})\.(\d{4})$'
    match = re.match(birthdate_pattern, message.text.strip())
    
    if not match:
        await message.answer("⚠️ Неправильний формат дати. Введіть дату у форматі ДД.ММ.РРРР (наприклад: 15.03.1995)")
        return
    
    day, month, year = map(int, match.groups())
    
    if not (1 <= day <= 31):
        await message.answer("⚠️ Неправильний день. День повинен бути від 01 до 31.")
        return
    
    if not (1 <= month <= 12):
        await message.answer("⚠️ Неправильний місяць. Місяць повинен бути від 01 до 12.")
        return
    
    if not (1900 <= year <= 2024):
        await message.answer("⚠️ Неправильний рік. Рік повинен бути від 1900 до 2024.")
        return
    
    await state.update_data(birthdate=message.text)
    await message.answer(
        "Якими мовами ти володієш. Вкажи рівень володіння. Наприклад: українська — рідна, англійська — B2.",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.set_state(CVStates.languages)

@router.message(CVStates.languages)
async def process_languages_input(message: types.Message, state: FSMContext):
    
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
        "Давайте спробуємо ще раз! Надішліть фото для твого CV",
        parse_mode="HTML",
        reply_markup=get_back_kb()
    )
    await state.clear()
    await state.set_state(CVStates.photo)


def draw_sidebar(canvas, doc):
    """Малює кольорову бокову панель зліва"""
    canvas.saveState()
    width, height = letter
    sidebar_width = 200  # зробимо ширше для фото + контактів
    canvas.setFillColor(colors.HexColor("#F5A020"))
    canvas.rect(0, 0, sidebar_width, height, stroke=0, fill=1)
    canvas.restoreState()

def generate_cv(data, user_name: str, photo_bytes: BytesIO | None):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor="#FFFFFF",
        spaceAfter=12,
        alignment=1,
        fontName="DejaVuSans-Bold"
    )
    sidebar_text_style = ParagraphStyle(
        'SidebarTextStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor="#FFFFFF",
        spaceAfter=8,
        fontName="DejaVuSans"
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor="#000000",
        spaceAfter=6,
        fontName="DejaVuSans-Bold"
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        spaceAfter=6,
        fontName="DejaVuSans"
    )
    sidebar_heading_style = ParagraphStyle( # Додамо стиль для заголовків у сайдбарі
        'SidebarHeadingStyle', parent=styles['Normal'], fontSize=11, 
        textColor="#FFFFFF", spaceAfter=4, fontName="DejaVuSans-Bold"
    )

    sidebar_story = []
    
    if photo_bytes:
        try:
            img = Image(photo_bytes, width=1.5*inch, height=1.8*inch)
            img.hAlign = "CENTER"
            sidebar_story.append(img)
            sidebar_story.append(Spacer(1, 0.2*inch))
        except Exception as e:
            print(f"Помилка обробки фото: {e}")

    sidebar_story.append(Paragraph(user_name, title_style))
    sidebar_story.append(Paragraph("Бажана посада", sidebar_heading_style))
    sidebar_story.append(Paragraph(data.get("position", "Не вказано"), sidebar_text_style))
    sidebar_story.append(Spacer(1, 0.3*inch))

    sidebar_story.append(Paragraph("Контакти", sidebar_heading_style))
    contacts_text = data.get("contacts", "Не вказано").replace('\n', '<br/>')
    sidebar_story.append(Paragraph(contacts_text, sidebar_text_style))
    sidebar_story.append(Spacer(1, 0.2*inch))
    
    sidebar_story.append(Paragraph("Дата народження", sidebar_heading_style))
    sidebar_story.append(Paragraph(data.get('birthdate', 'Не вказано'), sidebar_text_style))
    sidebar_story.append(Spacer(1, 0.2*inch))

    sidebar_story.append(Paragraph("Мови", sidebar_heading_style))
    languages_text = data.get("languages", "Не вказано").replace('\n', '<br/>')
    sidebar_story.append(Paragraph(languages_text, sidebar_text_style))


    main_story = []
    
    sections = [
        ("Про себе", data.get("about")),
        ("Досвід роботи", data.get("experience")),
        ("Освіта", f"{data.get('education', 'Не вказано')}<br/><i>{data.get('speciality', 'Не вказано')}</i>"),
        ("Навички", data.get("skills")),
    ]

    for label, content in sections:
        if content:
            main_story.append(Paragraph(label, heading_style))
            main_story.append(Paragraph(content, body_style))
            main_story.append(Spacer(1, 0.15*inch))

    width, height = letter
    sidebar_width = 200
    frame_sidebar = Frame(20, 20, sidebar_width-40, height-40, id='sidebar')
    frame_main = Frame(sidebar_width+10, 20, width-sidebar_width-30, height-40, id='main')
    
    template = PageTemplate(frames=[frame_sidebar, frame_main], onPage=draw_sidebar)
    doc.addPageTemplates([template])
    
    story = sidebar_story + [FrameBreak()] + main_story
    
    doc.build(story)
    
    buffer.seek(0)
    return buffer.read()


@router.message(F.text == "Так")
async def process_confirm_yes(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    try:
        user = await get_user(message.from_user.id)
        user_name = user.get("name", f"user_{message.from_user.id}")
        
        photo_bytes = None
        if file_id := data.get('photo'):
            photo_file = await bot.get_file(file_id)
            photo_bytes = await bot.download_file(photo_file.file_path)

        loop = asyncio.get_running_loop()
        pdf_bytes = await loop.run_in_executor(
            None, generate_cv, data, user_name, photo_bytes
        )
        
        document = BufferedInputFile(file=pdf_bytes, filename=f"CV_{user_name}.pdf")
        sent_doc = await message.answer_document(document)

        await add_cv(
            user_id=message.from_user.id,
            position=data.get("position"),
            languages=data.get("languages"),
            education=data.get("education"),
            speciality=data.get("speciality"),
            experience=data.get("experience"),
            skills=data.get("skills"),
            contacts=data.get("contacts"),
            about=data.get("about"),
            birthdate=data.get("birthdate"),
            cv_file_id=sent_doc.document.file_id
        )

        await message.answer(
            "✅ Ваше CV успішно створено!",
            reply_markup=main_menu_kb()
        )
    except Exception as e:
        print(f"Сталася помилка при генерації CV: {e}")
        await message.answer("❗ Сталася помилка під час створення PDF. Спробуйте ще раз.")
    finally:
        await state.clear()