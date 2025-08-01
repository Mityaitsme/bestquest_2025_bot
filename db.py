import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")

def get_random_riddle():
  try:
    print("Подключаюсь к базе данных...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT question FROM puzzles ORDER BY RANDOM() LIMIT 1;")
    result = cur.fetchone()
    conn.close()
    return result[0] if result else "В базе нет загадок."
  except Exception as e:
    print(f"Ошибка подключения к БД: {e}")
    return f"Ошибка подключения к БД: {e}"