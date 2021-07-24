"""
Simple Bot to handle '(my_)chat_member' updates.
Greets new users & keeps track of which chats the bot is in.
Usage:
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import os
import random
from datetime import datetime

from dotenv import load_dotenv
from loguru import logger
from telegram import Update
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

# Enable logging
from app.ml.nets import sberbank_small_gpt3


def repry(update, context):
    random.seed(datetime.now().timestamp())
    message: str = update['message']['text']
    private_chat: bool = update.effective_chat.type == 'private'
    pinged = update.message.bot['username'] in message
    if any((pinged, private_chat, random.randint(0, 30) == 5)):
        message = message if private_chat else message.replace(f'@{update.message.bot["username"]}', '').strip()
        update.message.reply_text(sberbank_small_gpt3(message, model_name="sberbank-ai/rugpt3small_based_on_gpt2",
                                                      max_length=random.randint(64, 128)))


def cmd_handler(update, context):
    user_says = " ".join(context.args)
    update.message.reply_text("You said: " + user_says)


def bot_idle() -> None:
    load_dotenv()
    token = os.getenv('TOKEN')
    sberbank_small_gpt3('1', model_name="sberbank-ai/rugpt3small_based_on_gpt2", max_length=24)
    updater = Updater(token)

    dispatcher = updater.dispatcher

    echo_handler = MessageHandler(Filters.text & (~Filters.command), repry)

    dispatcher.add_handler(echo_handler)
    dispatcher.add_handler(CommandHandler('net_stat', cmd_handler))
    dispatcher.add_handler(CommandHandler('set_stats', cmd_handler))

    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    updater.idle()
