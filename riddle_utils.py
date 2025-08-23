import random
from telebot.handler_backends import State
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from global_variables import *
from messages import *
from utils import *


@db_connection_utils
def send_riddle(cur, bot, chat_id, markup=None):
    cur.execute("SELECT cur_stage FROM teams WHERE id = %s", (chat_id,))
    cur_stage = cur.fetchone()[0]
    cur.execute("SELECT question FROM riddles WHERE id = %s", (cur_stage,))
    question = cur.fetchone()[0]
    if question != "SKIP":
        cur.execute("SELECT question_file_name FROM riddles WHERE id = %s", (cur_stage,))
        question_file_name = cur.fetchone()[0]
        safe_send_message(bot, chat_id, question, filename=question_file_name, markup=markup)


@db_connection_utils
def check_riddle(cur, chat_id, answer):
    cur.execute("SELECT cur_stage FROM teams WHERE id = %s", (chat_id,))
    cur_stage = cur.fetchone()[0]
    cur.execute("SELECT answer FROM riddles WHERE id = %s", (cur_stage,))
    correct_answer = cur.fetchone()[0]
    if correct_answer == "VERIFICATION":
        index = random.randint(1, WHILE_VERIFYING_COUNT)
        safe_send_message(bot, chat_id, while_verifying[index - 1])
        return correct_answer
    elif correct_answer == answer:
        return "CORRECT"
    else:
        return "WRONG"


@db_connection_utils
def send_hint(cur, bot, chat_id):
    cur_moment = cur_time()
    cur.execute("SELECT call_time FROM teams WHERE id = %s", (chat_id,))
    call_time = cur.fetchone()[0]
    if cur_moment - call_time < FIRST_HINT_TIME:
        index = random.randint(1, EARLY_HINT_LINE_COUNT)
        safe_send_message(bot, chat_id, too_early_for_a_hint[index - 1])
        return

    cur.execute("SELECT cur_stage FROM teams WHERE id = %s", (chat_id,))
    cur_stage = cur.fetchone()[0]
    cur.execute("SELECT hint FROM riddles WHERE id = %s", (cur_stage,))
    hint = cur.fetchone()[0]
    cur.execute("SELECT hint_file_name FROM riddles WHERE id = %s", (cur_stage,))
    hint_file_name = cur.fetchone()[0]
    safe_send_message(bot, chat_id, hint, filename=hint_file_name)


@db_connection_utils
def send_to_verification(cur, bot, original_message):
    cur.execute("SELECT team_name FROM teams WHERE id = %s", (original_message.chat.id,))
    team_name = cur.fetchone()[0]
    forwarded = bot.forward_message(
        chat_id=GOD_ID,
        from_chat_id=original_message.chat.id,
        message_id=original_message.message_id
    )

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("Да", callback_data=f"approve:{original_message.chat.id}:{team_name}"),
        InlineKeyboardButton("Нет", callback_data=f"reject:{original_message.chat.id}:{team_name}")
    )
    markup.row(
        InlineKeyboardButton("Да + ответить текстом", 
                             callback_data=f"approve+feedback:{original_message.chat.id}:{team_name}")
    )
    markup.row(
        InlineKeyboardButton("Нет + ответить текстом", 
                             callback_data=f"reject+feedback:{original_message.chat.id}:{team_name}")
    )

    bot.send_message(
        chat_id=GOD_ID,
        text=f"Одобрить ответ команды {team_name}?",
        reply_to_message_id=forwarded.message_id,
        reply_markup=markup
    )


@db_connection_utils
def approve_riddle(cur, bot, chat_id, feedback=None):
    cur.execute("SELECT team_name FROM teams WHERE id = %s", (chat_id,))
    team_name = cur.fetchone()[0]
    if feedback:
        forward_feedback(bot, feedback, chat_id)
        safe_send_message(bot, GOD_ID, f"Ответ одобрен, фидбек отправлен команде {team_name}.")
    else:
        index = random.randint(1, RIGHT_REPLIES_COUNT)
        safe_send_message(bot, chat_id, right_answers[index - 1])
    call_time = cur_time()

    cur.execute("""
        UPDATE teams
        SET cur_stage = CASE
                WHEN start_stage - cur_stage = 1 THEN %s + 1
                WHEN cur_stage - start_stage + 1 = %s THEN %s + 1
                WHEN cur_stage = %s THEN 1
                ELSE cur_stage + 1
            END,
            call_time = %s
        WHERE id = %s
        RETURNING cur_stage, start_stage;
    """, (RIDDLES_COUNT, RIDDLES_COUNT, RIDDLES_COUNT, RIDDLES_COUNT, call_time, chat_id))
    new_cur_stage, start_stage = cur.fetchone()

    if new_cur_stage <= RIDDLES_COUNT:
        safe_send_message(bot, GOD_ID, f"{team_name} верно решили загадку, текущий счёт: {(new_cur_stage + RIDDLES_COUNT - start_stage - 1) % RIDDLES_COUNT + 1}/{RIDDLES_COUNT}")
    elif new_cur_stage < ULTIMATE_RIDDLES_COUNT:
        safe_send_message(bot, GOD_ID, f"{team_name} в финальной стадии, текущий этап: {new_cur_stage - RIDDLES_COUNT}/{ULTIMATE_RIDDLES_COUNT - RIDDLES_COUNT - 1}")
    bot.set_state(chat_id, State.riddle, chat_id)
    return team_name, new_cur_stage


def right_answer_scenario(bot, chat_id, feedback=None):
    team_name, new_cur_stage = approve_riddle(bot, chat_id, feedback=feedback)
    markup = None
    if new_cur_stage ==  MONOLOGUE_ID:
        for line in monologue:
            safe_send_message(bot, chat_id, line)
    elif new_cur_stage in riddle_markups.keys():
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton(riddle_markups[new_cur_stage][0])
        btn2 = types.KeyboardButton(riddle_markups[new_cur_stage][1])
        markup.add(btn1, btn2)
    if new_cur_stage <= ULTIMATE_RIDDLES_COUNT:
        bot.set_state(chat_id, State.riddle, chat_id)
    else:
        bot.set_state(chat_id, State.escape_room, chat_id)
    send_riddle(bot, chat_id, markup=markup)
    if new_cur_stage == ULTIMATE_RIDDLES_COUNT:
        safe_send_message(bot, GOD_ID, f'Команда {team_name} завершила прохождение загадок.')
        bot.set_state(chat_id, State.escape_room, chat_id)


@db_connection_utils
def wrong_answer_scenario(cur, bot, chat_id, feedback=None):
    cur.execute("SELECT team_name FROM teams WHERE id = %s", (chat_id,))
    team_name = cur.fetchone()[0]
    safe_send_message(bot, GOD_ID, f"{team_name} неверно решили загадку.")
    if feedback:
        forward_feedback(bot, feedback, chat_id)
        bot.send_message(GOD_ID, f"Ответ отклонён, фидбек отправлен команде {team_name}.")
    else:
        index = random.randint(1, WRONG_REPLIES_COUNT)
        safe_send_message(bot, chat_id, wrong_answers[index - 1])
    bot.set_state(chat_id, State.riddle, chat_id)


def forward_feedback(bot, msg, target_chat_id):
    try:
        bot.copy_message(
            chat_id=target_chat_id,
            from_chat_id=msg.chat.id,
            message_id=msg.message_id
        )
        return
    except Exception as e:
        print(f"[WARN] copy_message не сработал: {e}. Пробую вручную...")

    # Ручная пересборка (на всякий случай, для редких типов)
    if msg.content_type == "text":
        safe_send_message(bot, target_chat_id, msg.text)
    elif msg.content_type == "photo":
        bot.send_photo(
            target_chat_id,
            msg.photo[-1].file_id,
            caption=msg.caption
        )
    elif msg.content_type == "document":
        bot.send_document(
            target_chat_id,
            msg.document.file_id,
            caption=msg.caption
        )
    elif msg.content_type == "video":
        bot.send_video(
            target_chat_id,
            msg.video.file_id,
            caption=msg.caption
        )
    elif msg.content_type == "audio":
        bot.send_audio(
            target_chat_id,
            msg.audio.file_id,
            caption=msg.caption
        )
    elif msg.content_type == "voice":
        bot.send_voice(
            target_chat_id,
            msg.voice.file_id,
            caption=msg.caption
        )
    elif msg.content_type == "sticker":
        bot.send_sticker(target_chat_id, msg.sticker.file_id)
    else:
        safe_send_message(bot, target_chat_id, "Error. Try again.")

