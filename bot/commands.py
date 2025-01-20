from aiogram.types import BotCommand
from aiogram import Bot

async def set_commands(bot: Bot):
    commands = [

        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/information", description="Инструкция"),
        BotCommand(command="/feedback", description="Оставить отзыв"),
    ]

    await bot.set_my_commands(commands)