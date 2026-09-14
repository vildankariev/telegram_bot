import aiosqlite
from config import DATABASE_NAME


# Инициализация базы данных (создание таблиц)
async def init_db():
    """Создает таблицы в базе данных при первом запуске"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        # Таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone TEXT UNIQUE,
                balance INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin', 'superadmin')),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Таблица транзакций (история операций)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER,
                user_id INTEGER,
                amount INTEGER,
                operation_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.commit()


# Проверка, зарегистрирован ли пользователь
async def is_user_registered(user_id: int) -> bool:
    """Проверяет, есть ли пользователь в базе"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            result = await cursor.fetchone()
            return result is not None


# Регистрация нового пользователя
async def register_user(user_id: int, username: str, first_name: str, phone: str):
    """Добавляет нового пользователя в базу"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            """INSERT INTO users (user_id, username, first_name, phone, role) 
               VALUES (?, ?, ?, ?, 'user')""",
            (user_id, username, first_name, phone)
        )
        await db.commit()


# Получение данных пользователя
async def get_user(user_id: int):
    """Возвращает данные пользователя по ID"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()


# Получение пользователя по номеру телефона
async def get_user_by_phone(phone: str):
    """Ищет пользователя по номеру телефона"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute(
                "SELECT * FROM users WHERE phone = ?", (phone,)
        ) as cursor:
            return await cursor.fetchone()


# Обновление баланса (прибавить/вычесть)
async def update_balance(user_id: int, amount: int):
    """Изменяет баланс пользователя (amount может быть отрицательным)"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "UPDATE users SET balance = balance + ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# Установка точного баланса
async def set_balance(user_id: int, amount: int):
    """Устанавливает точный баланс пользователю"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (amount, user_id)
        )
        await db.commit()


# Изменение роли пользователя
async def update_role(user_id: int, role: str):
    """Меняет роль пользователя (user/admin/superadmin)"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            "UPDATE users SET role = ? WHERE user_id = ?",
            (role, user_id)
        )
        await db.commit()


# Удаление пользователя
async def delete_user(user_id: int):
    """Удаляет пользователя из базы"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        await db.commit()


# Получение списка всех пользователей
async def get_all_users():
    """Возвращает список всех пользователей"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT * FROM users") as cursor:
            return await cursor.fetchall()


# Получение списка админов
async def get_admins():
    """Возвращает список всех админов"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute(
                "SELECT * FROM users WHERE role IN ('admin', 'superadmin')"
        ) as cursor:
            return await cursor.fetchall()


# Запись транзакции
async def log_transaction(admin_id: int, user_id: int, amount: int, operation_type: str):
    """Записывает операцию в историю транзакций"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        await db.execute(
            """INSERT INTO transactions (admin_id, user_id, amount, operation_type) 
               VALUES (?, ?, ?, ?)""",
            (admin_id, user_id, amount, operation_type)
        )
        await db.commit()


# Получение статистики
async def get_stats():
    """Возвращает статистику бота"""
    async with aiosqlite.connect(DATABASE_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as cursor:
            total_users = (await cursor.fetchone())[0]

        async with db.execute(
                "SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')"
        ) as cursor:
            total_admins = (await cursor.fetchone())[0]

        async with db.execute("SELECT SUM(balance) FROM users") as cursor:
            total_balance = (await cursor.fetchone())[0] or 0

        return {
            "total_users": total_users,
            "total_admins": total_admins,
            "total_balance": total_balance
        }