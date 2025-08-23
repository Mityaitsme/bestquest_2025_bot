import random
from telebot.handler_backends import State
from telebot import types
from utils import *
from riddle_utils import *
from messages import *
from global_variables import *


def activate_registration_handlers():
    @bot.message_handler(commands=['start'])
    @db_connection_handlers
    def start_quest(message, cur):
        chat_id = message.chat.id
        cur.execute("SELECT 1 FROM teams WHERE id = %s", (chat_id,))
        result = cur.fetchone()
        if result is not None:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Продолжить")
            markup.add(btn1)
            safe_send_message(bot, chat_id, start_m[1], markup=markup)
            bot.set_state(chat_id, State.go_on, chat_id)
        else:
            safe_send_message(bot, chat_id, start_m[0])
            bot.set_state(chat_id, State.name, chat_id)


    @bot.message_handler(state=State.go_on,
        content_types=DEFAULT_CONTENT_TYPES)
    @db_connection_handlers
    def continue_quest(message, cur):
        chat_id = message.chat.id
        cur.execute("SELECT cur_stage FROM teams WHERE id = %s", (chat_id,))
        cur_stage = cur.fetchone()[0]
        if cur_stage > 0 and cur_stage < ULTIMATE_RIDDLES_COUNT:
            send_riddle(bot, chat_id)
            bot.set_state(chat_id, State.riddle, chat_id)
        elif cur_stage == 0:
            bot.set_state(chat_id, State.get_stage, chat_id)
            safe_send_message(bot, chat_id, stage_m)
        else:
            bot.set_state(chat_id, State.escape_room, chat_id)
            safe_send_message(bot, chat_id, final_m)


    @bot.message_handler(state=State.name,
        content_types=DEFAULT_CONTENT_TYPES)
    @db_connection_handlers
    def register_team(message, cur):
        chat_id = message.chat.id
        team_name = message_text(message)
        if team_name != "":
            try:
                call_time = cur_time()
                cur.execute("SELECT 1 FROM teams WHERE team_name = %s", (team_name,))
                result = cur.fetchone()
                if result is None:
                    cur.execute("INSERT INTO teams (id, team_name, start_stage, cur_stage, call_time) VALUES "
                    "(%s, %s, 0, 0, %s)", (chat_id, team_name, call_time))
                    safe_send_message(bot, chat_id, stage_m)
                    bot.set_state(chat_id, State.get_stage, chat_id)
                else:
                    safe_send_message(bot, chat_id, wrong_name[0])
                    bot.set_state(chat_id, State.name, chat_id)
            except Exception as e:
                safe_send_message(bot, chat_id, wrong_name[1])
                bot.set_state(chat_id, State.name, chat_id)
        else:
            safe_send_message(bot, chat_id, wrong_name[1])
            bot.set_state(chat_id, State.name, chat_id)


    @bot.message_handler(state=State.get_stage,
        content_types=DEFAULT_CONTENT_TYPES)
    @db_connection_handlers
    def get_stage(message, cur):
        chat_id = message.chat.id
        try:
            start_stage = int(message_text(message).strip())
            cur.execute("SELECT team_name FROM teams WHERE id = %s", (chat_id,))
            team_name = cur.fetchone()[0]
            cur.execute("""
            UPDATE teams
            SET start_stage = %s,
                cur_stage = %s
            WHERE id = %s
            """, (start_stage, start_stage, chat_id))
            text = instructions_1_m[0] + team_name + instructions_1_m[1]
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton("Да")
            btn2 = types.KeyboardButton("Нет")
            markup.add(btn1, btn2)
            safe_send_message(bot, chat_id, text, markup=markup)
            bot.set_state(chat_id, State.participation_confirmation, chat_id)
        except Exception as e:
            safe_send_message(bot, chat_id, wrong_stage)
            bot.set_state(chat_id, State.get_stage, chat_id)


    @bot.message_handler(state=State.participation_confirmation,
        content_types=DEFAULT_CONTENT_TYPES)
    def participation_confirmation(message):
        chat_id = message.chat.id
        answer = message_text(message).strip().lower()
        if answer == "да":
            safe_send_message(bot, chat_id, instructions_3_m)
            send_riddle(bot, chat_id)
            bot.set_state(chat_id, State.riddle, chat_id)
        else:
            index = random.randint(1, 3)
            safe_send_message(bot, chat_id, instructions_2_m[index - 1])
            bot.set_state(chat_id, State.participation_confirmation, chat_id)