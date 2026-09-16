import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Токен бота из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID главного админа из .env
SUPERADMIN_ID = int(os.getenv("SUPERADMIN_ID"))

# Настройки Turso (облачная база данных)
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN")