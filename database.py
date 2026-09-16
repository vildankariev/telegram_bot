import asyncpg
from config import DATABASE_URL

# Глобальная переменная для хранения пула соединений
_pool = None

async def get_pool():
    """Возвращает пул соединений с базой данных"""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(DATABASE_URL)
    return _pool

async def init_db():
    """Создает таблицы в базе данных при первом запуске"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                phone TEXT UNIQUE,
                balance INTEGER DEFAULT 0,
                role TEXT DEFAULT 'user' CHECK(role IN ('user', 'admin', 'superadmin')),
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id SERIAL PRIMARY KEY,
                admin_id BIGINT,
                user_id BIGINT,
                amount INTEGER,
                operation_type TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

async def is_user_registered(user_id: int) -> bool:
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.fetchval("SELECT user_id FROM users WHERE user_id = $1", user_id)
        return result is not None

async def register_user(user_id: int, username: str, first_name: str, phone: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (user_id, username, first_name, phone, role) VALUES ($1, $2, $3, $4, 'user')",
            user_id, username, first_name, phone
        )

async def get_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)

async def get_user_by_phone(phone: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM users WHERE phone = $1", phone)

async def update_balance(user_id: int, amount: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = balance + $1 WHERE user_id = $2", amount, user_id)

async def set_balance(user_id: int, amount: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET balance = $1 WHERE user_id = $2", amount, user_id)

async def update_role(user_id: int, role: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET role = $1 WHERE user_id = $2", role, user_id)

async def delete_user(user_id: int):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE user_id = $1", user_id)

async def get_all_users():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM users")

async def get_admins():
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT * FROM users WHERE role IN ('admin', 'superadmin')")

async def log_transaction(admin_id: int, user_id: int, amount: int, operation_type: str):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO transactions (admin_id, user_id, amount, operation_type) VALUES ($1, $2, $3, $4)",
            admin_id, user_id, amount, operation_type
        )

async def get_stats():
    pool = await get_pool()
    async with pool.acquire() as conn:
        total_users = await conn.fetchval("SELECT COUNT(*) FROM users")
        total_admins = await conn.fetchval("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')")
        total_balance = await conn.fetchval("SELECT SUM(balance) FROM users") or 0
        return {
            "total_users": total_users,
            "total_admins": total_admins,
            "total_balance": total_balance
        }