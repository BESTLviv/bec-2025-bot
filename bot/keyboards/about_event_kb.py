from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_about_event_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Організатори🫂"), KeyboardButton(text="Що таке BEC⚙️")],
            [KeyboardButton(text="Категорії змагань✨"), KeyboardButton(text="Дата та місце проведення📅")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )

def get_about_categories_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Співпраця категорій🤝")], 
            [KeyboardButton(text="Приклади завдань😉")], 
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )