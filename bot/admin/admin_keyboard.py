from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_admin_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Розсилка")],
            [KeyboardButton(text="Статистика")],
            [KeyboardButton(text="Отримати всі CV")],
        ],
        resize_keyboard=True
    )

def get_statistic_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отримати всі команди")],
            [KeyboardButton(text="Отримати всі не повні команди")],
            [KeyboardButton(text="Отримати всі ID")],
            [KeyboardButton(text="Отримати всі TD")],
        ],
        resize_keyboard=True
    )
