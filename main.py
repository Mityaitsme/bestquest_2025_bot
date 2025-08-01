import telebot
from dotenv import load_dotenv
import os
import psycopg2
import random

load_dotenv()

BOT_TOKEN = os.getenv("TG_API_TOKEN")
DB_URL = os.getenv("DB_URL")

bot = telebot.TeleBot(BOT_TOKEN)

def safe_send_message(bot, chat_id, text):
    try:
        bot.send_message(chat_id, text)
    except telebot.apihelper.ApiTelegramException as e:
        if e.error_code == 403:
            print(f"❌ Пользователь {chat_id} недоступен.")
        else:
            raise

def get_db_connection():
    return psycopg2.connect(DB_URL)

@bot.message_handler(commands=['register'])
def register_team(message):
    chat_id = message.chat.id
    name = message.text.replace('/register', '').strip()

    if not name:
        safe_send_message(bot, chat_id, "Пожалуйста, укажи название команды после /register")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM teams WHERE id = %s", (chat_id,))
        existing = cur.fetchone()

        if existing:
            safe_send_message(bot, chat_id, f"Ты уже зарегистрирован как команда: {existing[1]}")
        else:
            cur.execute("INSERT INTO teams (id, name, progress) VALUES (%s, %s, %s)",
                        (chat_id, name, 0))
            conn.commit()
            safe_send_message(bot, chat_id, f"Команда '{name}' успешно зарегистрирована! Напиши /riddle, чтобы получить первую загадку.")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при регистрации: {e}")
        safe_send_message(bot, chat_id, "Произошла ошибка при регистрации. Попробуй позже.")

@bot.message_handler(commands=['riddle'])
def send_riddle(message):
    chat_id = message.chat.id
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Проверка на регистрацию
        cur.execute("SELECT progress FROM teams WHERE id = %s", (chat_id,))
        team = cur.fetchone()

        if not team:
            safe_send_message(bot, chat_id, "Ты ещё не зарегистрирован. Напиши /register <название команды>.")
            return

        # Получить случайную загадку
        cur.execute("SELECT id, question, answer FROM puzzles ORDER BY RANDOM() LIMIT 1;")
        riddle = cur.fetchone()
        if not riddle:
            safe_send_message(bot, chat_id, "Загадок пока нет в базе данных.")
            return

        riddle_id, question, answer = riddle

        # Сохраняем текущую загадку в памяти
        bot_riddles[chat_id] = (riddle_id, answer.lower())
        safe_send_message(bot, chat_id, f"Вот твоя загадка: {question}")

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при выдаче загадки: {e}")
        safe_send_message(bot, chat_id, "Произошла ошибка при получении загадки. Попробуй позже.")

@bot.message_handler(func=lambda message: True)
def handle_answer(message):
    chat_id = message.chat.id
    if chat_id not in bot_riddles:
        return  # загадка ещё не выдавалась

    _, correct_answer = bot_riddles[chat_id]
    user_answer = message.text.strip().lower()

    if user_answer == correct_answer:
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE teams SET progress = progress + 1 WHERE id = %s", (chat_id,))
            conn.commit()
            cur.close()
            conn.close()

            safe_send_message(bot, chat_id, "Верно! Чтобы получить следующую загадку, напиши /riddle")
            del bot_riddles[chat_id]  # сбрасываем текущую загадку
        except Exception as e:
            print(f"Ошибка при обновлении прогресса: {e}")
            safe_send_message(bot, chat_id, "Произошла ошибка при обновлении прогресса. Попробуй позже.")
    else:
        safe_send_message(bot, chat_id, "Неверно. Попробуй ещё раз!")

bot_riddles = {}

print("Бот запущен!")
bot.polling()
