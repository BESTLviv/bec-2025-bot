from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_not_team_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Створити команду🥇"), 
            KeyboardButton(text="Увійти в команду🏅")], 
            [KeyboardButton(text="Пошук команди🔍"),
            KeyboardButton(text="Назад до головного меню🏠")],
        ],
        resize_keyboard=True
    )

def get_category_kb(with_back=False):
    keyboard = [
        [KeyboardButton(text="Team Design")],
        [KeyboardButton(text="Innovative Design")],
        [KeyboardButton(text="Детальніше про категорії")],
    ]
    if with_back:
        keyboard.append([KeyboardButton(text="⬅️ Назад")])
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )