from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_cv_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Створити CV")], 
            [KeyboardButton(text="📤 Надіслати готове CV")],
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )

def get_back_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад")],
        ],
        resize_keyboard=True
    )

def get_is_correct_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Так")],
            [KeyboardButton(text="Ні")],
        ],
        resize_keyboard=True
    )