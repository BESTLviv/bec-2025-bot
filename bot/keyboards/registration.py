from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_uni_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎓 НУ “ЛП”"), KeyboardButton(text="🎓 ЛНУ ім. І. Франка")],
            [KeyboardButton(text="🎓 УКУ"), KeyboardButton(text="🎓 ЛНАМ")],
            [KeyboardButton(text="🎓 ЛДУБЖД"), KeyboardButton(text="🎓 ІТ Степ Університет")],
            [KeyboardButton(text="🎓 Інший")]
        ],
        resize_keyboard=True
    )

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Більше інфи")],
            [KeyboardButton(text="Лінка на групу для пошуку тімки")],
            [KeyboardButton(text="Моя команда")],
        ],
        resize_keyboard=True
    )

def get_course_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔹 1 курс"), KeyboardButton(text="🔹2 курс")],
            [KeyboardButton(text="🔹 3 курс"), KeyboardButton(text="🔹 4 курс")],
            [KeyboardButton(text="🔹 Магістратура")],
            [KeyboardButton(text="🔹 Не навчаюсь"), KeyboardButton(text="🔹 Ще у школі/коледжі")]
        ],
        resize_keyboard=True
    )