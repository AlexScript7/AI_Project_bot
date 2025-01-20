from aiogram import Router, F
from aiogram import Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from bot.inline_handlers import router as inline_router
from bot.advice_bot import get_response
from bot.database_create import get_user, insert_user, update_user, save_feedback, get_program_recommendation
from bot.keyboards import create_dynamic_menu
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from bot.links import links 

class UserState(StatesGroup):
    waiting_feedback = State()
    waiting_name = State()
    
user_context = {}

router = Router()

scheduler = AsyncIOScheduler()

async def send_notification(user_id: int, bot: Bot):
    await bot.send_message(user_id, "Определим направление?")

@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user:
        username, chat_enabled = user
        await message.answer(
            f"Мы вас помним, {username}!",
            reply_markup=create_dynamic_menu(chat_enabled)
        )

    else:
        await insert_user(user_id, {"name": None, "chat_enabled": False})
        await message.answer("Привет, как Вас зарегистрировать?")
        await state.set_state(UserState.waiting_name)
    bot = message.bot
    scheduler.add_job(
        send_notification, 
        trigger=IntervalTrigger(hours=48),
        args=[user_id, bot],
        max_instances=6
    )
    scheduler.start()

@router.message(UserState.waiting_feedback)
async def save_feedback_handler(message: Message, state: FSMContext):
    feedback_text = message.text
    user_id = message.from_user.id

    await save_feedback(user_id, feedback_text)
    await message.reply("Благодарим за отзыв!")
    await state.clear()

@router.message(Command("feedback"))
async def feedback_handler(message: Message, state: FSMContext):
    await state.set_state(UserState.waiting_feedback)
    await message.reply("Пожалуйста, оставьте свой отзыв:")

@router.message(Command("information"))
async def info_handler(message: Message):
    instruction_text = (
        "Команды:\n\n"
        "'Включить чат'/'Выключить чат' — общение с ассистентом\n"
        "'Сменить имя' — Поменять имя в боте\n"
        "'Материалы' —  Ссылки и материалы\n"
        "/start — Запустить бота\n"
        "/information — Инструкции\n"
        "/feedback — Оставить отзыв\n"
    )
    await message.answer(instruction_text, parse_mode="Markdown")

@router.message(F.text == "Включить чат")
async def chat_start_handler(message: Message):
    user_id = message.from_user.id
    await update_user(user_id, {"chat_enabled": True})
    await message.answer("Подбор программы включен.", reply_markup=create_dynamic_menu(True))
    await message.answer("Готовы подобрать программу?")

@router.message(F.text == "Выключить чат")
async def chat_end_handler(message: Message):
    user_id = message.from_user.id
    await update_user(user_id, {"chat_enabled": False})
    await message.answer("Подбор программы выключен.", reply_markup=create_dynamic_menu(False))

@router.message(UserState.waiting_name)
async def change_username(message: Message, state: FSMContext):
    new_username = message.text
    user_id = message.from_user.id

    await update_user(user_id, {"name": new_username})
    await message.reply(f"Вы записаны как {new_username}!")
    await state.clear()

@router.message(F.text == "Сменить имя")
async def change_username_prompt(message: Message, state: FSMContext):
    await state.set_state(UserState.waiting_name)
    await message.reply("Введите новое имя:")

@router.message(F.text == "Материалы")
async def show_options_handler(message: Message):
    """
    Обработчик кнопки "Материалы". Отправляет список ссылок в виде inline-клавиатуры.
    """
    if not links:
        await message.answer("Материалы пока недоступны.")
        return

    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, url=url)] for url, name in links
        ]
    )
    await message.answer("Доступные материалы:", reply_markup=inline_keyboard)

async def send_long_message(message, text):
    max_length = 4000
    for i in range(0, len(text), max_length):
        part = text[i:i + max_length]
        await message.answer(part)

@router.message()
async def conversation_handler(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user and user[1]:
        user_message = message.text
        if user_id in user_context:
            current_step = user_context[user_id].get("step", 0)
            user_context[user_id][f"answer_{current_step}"] = user_message

            question, next_step = await ask_user_questions(user_id, current_step)

            if next_step is None:
                await send_long_message(message, question) 
            else:
                user_context[user_id]["step"] = next_step
                await message.answer(question)
        else:
            question, next_step = await ask_user_questions(user_id)
            user_context[user_id] = {"step": next_step}
            await send_long_message(message, question)
    else:
        await message.answer("Включите чат, чтобы начать подбор.")

async def ask_user_questions(user_id: int, current_step: int = 0):
    questions = [
        "Какие предметы вы сдавали на ЕГЭ в школе?",
        "Какой у Вас профиль подготовки (технический, гуманитарный)?",
        "Какой у вас уровень подготовки в соответствии с баллами ЕГЭ (низкий, средний, высокий)?",
        "Знаете ли вы языки программирования?",
        "Какие темы Вам интересны?",
    ]

    if user_id not in user_context:
        user_context[user_id] = {}
    
    if current_step < len(questions):
        user_context[user_id]["step"] = current_step + 1
        return questions[current_step], current_step + 1

    else:
        recommendations = await get_program_recommendation(user_context[user_id])
        if recommendations:
            program, desc, link = recommendations[0]
            response = f"Мне кажется, вот подходящее направление:\n\n- {program} ({link})\n\n - {desc}"
        else:
            response = "Подходящих направлений не было найдено :("
        
        user_context.pop(user_id, None)
        return response, None

router.include_router(inline_router)
