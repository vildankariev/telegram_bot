import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Токен бота из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID главного админа из .env
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID"))
DATABASE_URL = os.getenv("DATABASE_URL")
