from aiogram import Router, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import aiosqlite
from bot.database_create import fetch_programs_from_db

router = Router()

def generate_program_buttons(programs):
    keyboard = InlineKeyboardMarkup()
    for program_name, url in programs:
        keyboard.add(InlineKeyboardButton(text=program_name, url=url))
    return keyboard

@router.callback_query(F.data == "option")
async def option_1_handler(callback_query: CallbackQuery):
    programs = await fetch_programs_from_db()
    if programs:
        response = "Доступные программы МИЭМ:\n\n"
        for program_name, url in programs:
            response += f"- {program_name} - [Ссылка]({url})\n"
        await callback_query.message.answer(response, parse_mode="Markdown")
    else:
        await callback_query.message.answer("В базе нет программ.")
    await callback_query.answer()

