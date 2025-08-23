import os
from dotenv import load_dotenv
from telebot.storage import StateMemoryStorage
import telebot
from telebot.handler_backends import State, StatesGroup
from telebot import custom_filters


RIDDLES_COUNT = 5 # количество загадок на стадии riddle, поменять!
ULTIMATE_RIDDLES_COUNT = 7 # количество загадок всего, поменять!
ZERO_MOMENT = 223456 # ПОМЕНЯТЬ ЧИСЛО (8.25.25 8:00:00)
FIRST_HINT_TIME = 18 # возможно 15, в секундах!!
SECOND_HINT_TIME = 25 # возможно 22, в секундах!!
WRONG_REPLIES_COUNT = 4 # может измениться, см messages.py
RIGHT_REPLIES_COUNT = 4 # может измениться, см messages.py
EARLY_HINT_LINE_COUNT = 3 # может измениться, см messages.py
WHILE_VERIFYING_COUNT = 3 # может измениться, см messages.py
MONOLOGUE_ID = 44
MEME_COUNT = 1

FEEDBACK_MAP = {}
DEFAULT_CONTENT_TYPES = ["text", "photo", "document", "video", "audio", "voice", "sticker", "animation", "video_note", "location", "contact", "poll"]
riddle_markups = {5: ["Да", "Да"], 52: ["Преступник 1", "Преступник 2"]} # добавить имена, менять id


load_dotenv()
BOT_TOKEN = os.getenv("TG_API_TOKEN")
DB_URL = os.getenv("DB_URL")
GOD_ID = int(os.getenv("GOD_ID"))

state_storage = StateMemoryStorage()
class State(StatesGroup):
    name = State()
    go_on = State()
    start = State()
    get_stage = State()
    riddle = State()
    participation_confirmation = State()
    answer_verification = State()
    verification_feedback = State()
    escape_room = State()

def create_bot(token):
    bot = telebot.TeleBot(token, state_storage=state_storage)
    bot.add_custom_filter(custom_filters.StateFilter(bot))
    return bot

bot = create_bot(BOT_TOKEN)
