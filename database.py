import libsql_client
from config import TURSO_DATABASE_URL, TURSO_AUTH_TOKEN


# Создаем клиент базы данных (подключение к Turso)
def get_db():
    """Возвращает подключение к облачной базе Turso"""
    return libsql_client.create_client(
        url=TURSO_DATABASE_URL,
        auth_token=TURSO_AUTH_TOKEN
    )


# Инициализация базы данных (создание таблиц)
async def init_db():
    """Создает таблицы в базе данных при первом запуске"""
    db = get_db()

    # Таблица пользователей
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            phone TEXT UNIQUE,
            balance INTEGER DEFAULT 0,
            role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin', 'superadmin')),
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.close()


# Проверка, зарегистрирован ли пользователь
async def is_user_registered(user_id: int) -> bool:
    """Проверяет, есть ли пользователь в базе"""
    db = get_db()
    result = await db.execute(
        "SELECT user_id FROM users WHERE user_id = ?", [user_id]
    )
    db.close()
    return len(result.rows) > 0


# Регистрация нового пользователя
async def register_user(user_id: int, username: str, first_name: str, phone: str):
    """Добавляет нового пользователя в базу"""
    db = get_db()
    await db.execute(
        """INSERT INTO users (user_id, username, first_name, phone, role) 
           VALUES (?, ?, ?, ?, 'user')""",
        [user_id, username, first_name, phone]
    )
    db.close()


# Получение данных пользователя
async def get_user(user_id: int):
    """Возвращает данные пользователя по ID"""
    db = get_db()
    result = await db.execute(
        "SELECT * FROM users WHERE user_id = ?", [user_id]
    )
    db.close()
    if len(result.rows) > 0:
        return result.rows[0]
    return None


# Получение пользователя по номеру телефона
async def get_user_by_phone(phone: str):
    """Ищет пользователя по номеру телефона"""
    db = get_db()
    result = await db.execute(
        "SELECT * FROM users WHERE phone = ?", [phone]
    )
    db.close()
    if len(result.rows) > 0:
        return result.rows[0]
    return None


# Обновление баланса (прибавить/вычесть)
async def update_balance(user_id: int, amount: int):
    """Изменяет баланс пользователя (amount может быть отрицательным)"""
    db = get_db()
    await db.execute(
        "UPDATE users SET balance = balance + ? WHERE user_id = ?",
        [amount, user_id]
    )
    db.close()


# Установка точного баланса
async def set_balance(user_id: int, amount: int):
    """Устанавливает точный баланс пользователю"""
    db = get_db()
    await db.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?",
        [amount, user_id]
    )
    db.close()


# Изменение роли пользователя
async def update_role(user_id: int, role: str):
    """Меняет роль пользователя (user/admin/superadmin)"""
    db = get_db()
    await db.execute(
        "UPDATE users SET role = ? WHERE user_id = ?",
        [role, user_id]
    )
    db.close()


# Удаление пользователя
async def delete_user(user_id: int):
    """Удаляет пользователя из базы"""
    db = get_db()
    await db.execute("DELETE FROM users WHERE user_id = ?", [user_id])
    db.close()


# Получение списка всех пользователей
async def get_all_users():
    """Возвращает список всех пользователей"""
    db = get_db()
    result = await db.execute("SELECT * FROM users")
    db.close()
    return result.rows


# Получение списка админов
async def get_admins():
    """Возвращает список всех админов"""
    db = get_db()
    result = await db.execute(
        "SELECT * FROM users WHERE role IN ('admin', 'superadmin')"
    )
    db.close()
    return result.rows


# Запись транзакции
async def log_transaction(admin_id: int, user_id: int, amount: int, operation_type: str):
    """Записывает операцию в историю транзакций"""
    db = get_db()
    await db.execute(
        """INSERT INTO transactions (admin_id, user_id, amount, operation_type) 
           VALUES (?, ?, ?, ?)""",
        [admin_id, user_id, amount, operation_type]
    )
    db.close()


# Получение статистики
async def get_stats():
    """Возвращает статистику бота"""
    db = get_db()

    # Всего пользователей
    result1 = await db.execute("SELECT COUNT(*) FROM users")
    total_users = result1.rows[0][0]

    # Админов
    result2 = await db.execute(
        "SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')"
    )
    total_admins = result2.rows[0][0]

    # Сумма всех балансов
    result3 = await db.execute("SELECT SUM(balance) FROM users")
    total_balance = result3.rows[0][0] or 0

    db.close()

    return {
        "total_users": total_users,
        "total_admins": total_admins,
        "total_balance": total_balance
    }