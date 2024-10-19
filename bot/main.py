import asyncio
import logging
import datetime
import time
import sys
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand

from log_changed_handler import LogChangedHandler
from watchdog.observers import Observer
from threading import Event

from db_worker import DBWorker


LOGS_FOLDER = os.getenv("LOGS_FOLDER", "logs/")

with open("TOKEN.txt", "rt") as file:
    TOKEN = file.readline().strip()

LOG_LEVEL = {"ERROR": 3, "INFO": 6, "DEBUG": 7}
bot_commands = [
    BotCommand(command="/start", description="Subscride to logs notifications"),
    BotCommand(command="/error", description="Set log level to ERROR"),
    BotCommand(command="/info", description="Set log level to INFO"),
    BotCommand(command="/debug", description="Set log level to DEBUG"),
    BotCommand(command="/stop", description="Unsubsribe from logs notifications"),
]


dp = Dispatcher()
db = DBWorker("db.sqlite3")


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    '/start' command receiver. Adds user to local database to send notifications
    """
    db.delete_chat(str(message.chat.id))
    db.insert_chat(str(message.chat.id))
    await message.answer(
        (
            f"Hello, {message.from_user.full_name}! "
            "I'll send you all ERROR messages from logs.\n"
            "Commands:\n"
            "/error - set log level to ERROR\n"
            "/info - set log level to INFO\n"
            "/debug - set log level to DEBUG\n"
            "/stop - stop sending logs"
        )
    )


@dp.message(Command(commands=["error", "info", "debug"]))
async def command_set_log_level(message: Message):
    """
    Set new log level for current user
    """
    new_log_level = message.text.split()[0][1:].upper()
    chat_ids = [i[0] for i in db.get_chats()]
    if str(message.chat.id) in chat_ids:
        db.set_log_level(str(message.chat.id), new_log_level)
        answer = f"Log level set to {new_log_level}"
    else:
        answer = "You aren't followed to notifications"
    await message.answer(answer)


@dp.message(Command(commands=["stop"]))
async def command_stop(message: Message):
    """
    Stop sending messages to current user
    """
    chat_ids = [i[0] for i in db.get_chats()]
    if str(message.chat.id) in chat_ids:
        db.delete_chat(str(message.chat.id))
        answer = "Sending logs is stopped"
    else:
        answer = "You aren't followed to notifications"
    await message.answer(answer)


async def notify_users(bot: Bot, last_time: float):
    """
    Send messages with new log messages to all users
    """
    with open(LOGS_FOLDER + "logs.log", "rt") as file:
        log_lines = file.readlines()
    chats = db.get_chats()
    for line_ in log_lines:
        line = line_.strip()
        # skip empty lines
        if not line:
            continue
        timestr, log_level, text = line.split(maxsplit=2)
        timestamp = int(
            datetime.datetime.strptime(timestr, "%Y-%m-%dT%H:%M:%SZ").timestamp()
        )
        # skip old messages
        if timestamp < last_time:
            continue
        timestr = datetime.datetime.fromtimestamp(timestamp).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        # remove '[' and ']'
        log_level = log_level[1:-1]

        message_text = f"{timestr} [{log_level}]: {text}"
        for chat_id, user_log_level in chats:
            if LOG_LEVEL[user_log_level] >= LOG_LEVEL[log_level]:
                await bot.send_message(chat_id=chat_id, text=message_text)
        last_time = timestamp
    return last_time + 0.1


async def logs_monitoring(bot: Bot):
    """
    Start observer and notify users on logs changed
    """
    handler = LogChangedHandler()
    obs = Observer()
    obs.schedule(handler, path=LOGS_FOLDER, recursive=False)
    obs.start()
    try:
        last_time = time.time()
        while True:
            await asyncio.sleep(1)
            if handler.event.is_set():
                last_time = await notify_users(bot, last_time)
                handler.event.clear()
    except:
        obs.stop()
    obs.join()


async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.set_my_commands(bot_commands)
    await asyncio.gather(dp.start_polling(bot), logs_monitoring(bot))


if __name__ == "__main__":
    event = Event()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
