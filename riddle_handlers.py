import random
from telebot.handler_backends import State
from utils import *
from riddle_utils import *
from messages import *
from global_variables import *


def activate_riddle_handlers():
    @bot.message_handler(state=State.riddle,
    content_types=DEFAULT_CONTENT_TYPES)
    def riddle_handler(message):
        chat_id = message.chat.id
        answer = message_text(message).strip().lower()
        if answer == "/hint":
            send_hint(bot, chat_id)
        else:
            checking_result = check_riddle(chat_id, answer)
            if checking_result == "VERIFICATION":
                send_to_verification(bot, message)
                bot.set_state(chat_id, State.answer_verification, chat_id)
            elif checking_result == "CORRECT":
                right_answer_scenario(bot, chat_id)
            elif checking_result == "WRONG":
                wrong_answer_scenario(bot, chat_id)
    

    @bot.message_handler(state=State.escape_room,
    content_types=DEFAULT_CONTENT_TYPES)
    def final_cycle(message):
        chat_id = message.chat.id
        text = message_text(message).strip().lower()
        if text == "/meme":
            index = random.randint(1, MEME_COUNT)
            filename = f"meme{index}.jpg"
            safe_send_message(bot, chat_id, "", filename=filename)
        else:
            safe_send_message(bot, chat_id, final_m)
