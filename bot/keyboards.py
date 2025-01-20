from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def create_dynamic_menu(chat_enabled: bool) -> ReplyKeyboardMarkup:
    button_text = "Выключить чат" if chat_enabled else "Включить чат"
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_text), KeyboardButton(text="Материалы")],
            [KeyboardButton(text="Сменить имя")],
        ],
        resize_keyboard=True
    )
