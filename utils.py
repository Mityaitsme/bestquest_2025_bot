import telebot
import psycopg2
import time
from functools import wraps
from global_variables import *


def safe_send_message(bot, chat_id, text, filename=None, markup=None):
    try:
        if filename == None:
            bot.send_message(chat_id, text, reply_markup=markup)
        else:
            with open(filename, 'rb') as file:
                if str(filename).endswith('.ogg'):
                    bot.send_voice(chat_id, file, reply_markup=markup, caption=text)
                elif str(filename).endswith('.jpg'):
                    bot.send_photo(chat_id, file, reply_markup=markup, caption=text)
                elif str(filename).endswith('.mp4'):
                    bot.send_video(chat_id, file, reply_markup=markup, caption=text, timeout=60)
                    # кружочки надо будет отдельно прописывать, если будут
                else:
                    bot.send_document(chat_id, file, reply_markup=markup, caption=text)
    except telebot.apihelper.ApiTelegramException as e:
        print(f"[WARN] safe_send_message не сработал: {e}.")
        if e.error_code == 403:
            print(f"Пользователь {chat_id} недоступен.")
        else:
            raise


def db_connection_utils(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            result = func(cur, *args, **kwargs)
            conn.commit()
            cur.close()
            return result
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    return wrapper


def db_connection_handlers(func):
    @wraps(func)
    def wrapper(message):
        conn = None
        try:
            conn = psycopg2.connect(DB_URL)
            cur = conn.cursor()
            result = func(message, cur)
            conn.commit()
            cur.close()
            return result
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
    return wrapper


def cur_time():
    return (int(time.time()) - ZERO_MOMENT) % 1000000


def message_text(msg):
    if msg.text:
        return msg.text
    if msg.caption:
        return msg.caption
    return ""
