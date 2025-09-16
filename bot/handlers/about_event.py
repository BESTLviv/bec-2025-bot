from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, FSInputFile
from bot.keyboards.about_event_kb import get_about_event_kb, get_about_categories_kb
from bot.keyboards.registration import get_reg_kb, main_menu_kb
from bot.utils.database import is_user_registered

router = Router()

class AboutEventStates(StatesGroup):
    about_event = State()
    categories = State()

@router.message(F.text == "Детальніше про змагання🧐")
async def handle_more_info(message: types.Message, state: FSMContext):
    try:
        photo_path = "assets/more.png"
        photo_to_send = FSInputFile(photo_path)

        await state.set_state(AboutEventStates.about_event)
        await message.answer_photo(
            photo=photo_to_send,
            caption="Тут ти дізнаєшся більше про змагання, організаторів, дати та категорії. Обирай, що цікавить!",
            parse_mode="HTML",
            reply_markup=get_about_event_kb()
        )
    except Exception as e:
        await message.answer("Сталася помилка. Спробуйте пізніше.")
        print(f"An error occurred: {str(e)}")  

@router.message(F.text == "Організатори🫂")
async def handle_organizers(message: types.Message, state: FSMContext):
    await state.set_state(AboutEventStates.about_event) 
    await message.answer(
        "BEST Lviv (Board of European Students of Technology) – осередок міжнародної громадської організації, який об’єднує студентів технічних спеціальностей. Нашою місією є розвиток студентів через обмін знаннями та співпраці компаній, університетів та студентів Європи.",
        parse_mode="HTML",
        reply_markup=get_about_event_kb()
    )

@router.message(F.text == "Що таке BEC⚙️")
async def handle_what_is_bec(message: types.Message, state: FSMContext):
    await state.set_state(AboutEventStates.about_event) 
    await message.answer(
        "BEST Engineering Competition (BEC) – безкоштовні інженерні змагання для студентів. Тут ти будеш створювати прототипи або концепти пристроїв разом з командою. Також на тебе чекають нетворкінг з представниками компаній, корисні лекції, воркшопи, коло однодумців та неймовірні призи!\n\nТема змагань: Повоєнне відновлення",
        parse_mode="HTML",
        reply_markup=get_about_event_kb()
    )

@router.message(F.text == "Дата та місце проведення📅")
async def handle_event_date_place(message: types.Message, state: FSMContext):
    await state.set_state(AboutEventStates.about_event) 
    await message.answer(
        "Відмічай в календарі 24-28 жовтня! Саме тоді будуть змагання.\n\nBEC попередньо відбудеться на офісі компанії GlobalLogic, що знаходиться за адресою <a href='https://www.google.com/maps/place/GlobalLogic+LWO7/data=!4m2!3m1!1s0x0:0x14eebe406256a875?sa=X&ved=1t:2428&ictx=111'>вулиця Козельницька, 1А</a>.\n\nЯкщо щось зміниться – тебе обов'язково попередять організатори.",
        parse_mode="HTML",
        reply_markup=get_about_event_kb()
    )

@router.message(F.text == "Категорії змагань✨")
async def handle_event_categories(message: types.Message, state: FSMContext):
    photo_path = "assets/tdid.png"
    photo_to_send = FSInputFile(photo_path)
    await state.set_state(AboutEventStates.categories)  
    await message.answer_photo(
        photo=photo_to_send,
        caption="То що ж, познайомишся з нашими категоріями? А ще вони можуть співпрацювати🤫.\n\nInnovative Design\n\nКонцептуальна категорія, де ти з командою придумуєш нове або вдосконалене інженерне рішення для реальної проблеми. Ваше завдання – показати, як це працює: через креслення або 3D-моделі. Тут важлива креативність, інноваційність і реалістичність твоєї ідеї.\n\nTeam Design\n\nПрактична інженерна категорія, де ти з командою будеш розв'язувати технічні задачі – у стилі ось проблема – зробіть пристрій, який її вирішує. Електроніка, механіка, IoT, embedded – все це про Team Design. На виході – робочий прототип.",
        parse_mode="HTML",
        reply_markup=get_about_categories_kb()
    )

@router.message(F.text == "Співпраця категорій🤝")
async def handle_categories_collaboration(message: types.Message, state: FSMContext):
    await state.set_state(AboutEventStates.categories)
    await message.answer(
        "Один з днів змагань – команди Innovative Design аналізують проблему та пропонують ідеї, як її вирішити.\n\nНаступного дня – команди Team Design беруть ці ідеї й втілюють їх у реальні прототипи.\n\nІ можливо, саме ваша ідея або пристрій стане основою для майбутнього стартапу.",
        parse_mode="HTML",
        reply_markup=get_about_categories_kb()
    )

@router.message(F.text == "Приклади завдань😉")
async def handle_task_examples(message: types.Message, state: FSMContext):
    await state.set_state(AboutEventStates.categories)
    await message.answer(
        "Приклад Team Design: Розробити функціональну модель тральника для пошуку та розмінування морських мін, який може керуватися в ручному та автоматичному режимі.\n\nПриклад Innovative Design: Розробити концепцію дрона, який сканує руйнування будівель для подальшого аналізу та планування відбудови",
        parse_mode="HTML",
        reply_markup=get_about_categories_kb()
    )

@router.message(F.text == "Назад")
async def handle_back(message: types.Message, state: FSMContext):
    isReg = await is_user_registered(message.from_user.id)
    if isReg:
        await message.answer(
            "Повертаємося до головного меню...",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
        await state.clear()
    else:
        await message.answer(
            "Повертаємося до загального меню про змагання...",
            parse_mode="HTML",
            reply_markup=get_about_event_kb()
        )
        await state.set_state(AboutEventStates.about_event)