import asyncio
import logging
import socket
socket.setdefaulttimeout(30)
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, Contact
from config import BOT_TOKEN, SUPERADMIN_ID
from database import (
    init_db, is_user_registered, register_user, get_user,
    get_user_by_phone, update_balance, set_balance, update_role,
    delete_user, get_all_users, get_admins, log_transaction, get_stats
)
from keyboards import get_user_menu, get_admin_menu, get_phone_keyboard

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем бота и диспетчер
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ==================== КОМАНДЫ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ====================

@dp.message(CommandStart())
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Проверяем, зарегистрирован ли пользователь
    if await is_user_registered(user_id):
        user = await get_user(user_id)
        role = user[5]  # Поле role

        # Показываем меню в зависимости от роли
        if role == 'superadmin':
            await message.answer(
                f"👋 С возвращением, Главный Админ!\n\n"
                f"🆔 Ваш ID: {user_id}\n"
                f"💰 Баланс: {user[4]} жетонов\n"
                f"👑 Роль: Главный администратор",
                reply_markup=get_admin_menu()
            )
        elif role == 'admin':
            await message.answer(
                f"👋 С возвращением, Админ!\n\n"
                f"🆔 Ваш ID: {user_id}\n"
                f"💰 Баланс: {user[4]} жетонов\n"
                f"🔰 Роль: Администратор",
                reply_markup=get_admin_menu()
            )
        else:
            await message.answer(
                f"👋 С возвращением, {message.from_user.first_name}!\n\n"
                f"🆔 Ваш ID: {user_id}\n"
                f"💰 Баланс: {user[4]} жетонов",
                reply_markup=get_user_menu()
            )
    else:
        # Новый пользователь - просим зарегистрироваться
        await message.answer(
            "👋 Привет! Я помощник однорукого джо!\n\n"
            "Хочешь получить жетоны моего друга? Тогда зарегистрируйся!\n"
            "Нажми кнопку ниже 👇",
            reply_markup=get_phone_keyboard()
        )


@dp.message(F.contact)
async def handle_contact(message: Message):
    """Обработчик получения контакта"""
    user_id = message.from_user.id

    # Проверяем, не зарегистрирован ли уже
    if await is_user_registered(user_id):
        await message.answer("✅ Вы уже зарегистрированы!")
        return

    # Регистрируем пользователя
    phone = message.contact.phone_number  # <-- ИСПРАВЛЕНО: берем из message
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""

    await register_user(user_id, username, first_name, phone)

    # Если это супер-админ, назначаем роль
    if user_id == SUPERADMIN_ID:
        await update_role(user_id, 'superadmin')
        role_text = "👑 Вы автоматически назначены Главным администратором!"
        menu = get_admin_menu()
    else:
        role_text = ""
        menu = get_user_menu()

    await message.answer(
        f"✅ Регистрация успешна!\n\n"
        f"🆔 Ваш ID: {user_id}\n"
        f"📱 Телефон: {phone}\n"
        f"💰 Баланс: 0 жетонов\n\n"
        f"{role_text}\n\n"
        f"⚠️ Сохраните свой ID — он понадобится для пополнения баланса.",
        reply_markup=menu
    )

    logger.info(f"Новый пользователь зарегистрирован: {user_id} ({first_name})")
    await register_user(user_id, username, first_name, phone)

    # Если это супер-админ, назначаем роль
    if user_id == SUPERADMIN_ID:
        await update_role(user_id, 'superadmin')
        role_text = "👑 Вы автоматически назначены Главным администратором!"
        menu = get_admin_menu()
    else:
        role_text = ""
        menu = get_user_menu()

    await message.answer(
        f"✅ Регистрация успешна!\n\n"
        f"🆔 Ваш ID: {user_id}\n"
        f"📱 Телефон: {phone}\n"
        f"💰 Баланс: 0 жетонов\n\n"
        f"{role_text}\n\n"
        f"⚠️ Сохраните свой ID — он понадобится для пополнения баланса.",
        reply_markup=menu
    )

    logger.info(f"Новый пользователь зарегистрирован: {user_id} ({first_name})")


@dp.message(F.text == "💰 Мой баланс")
async def show_balance(message: Message):
    """Показывает баланс пользователя"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user:
        await message.answer(
            f"💰 Ваш текущий баланс: {user[4]} жетонов\n"
            f"🆔 Ваш ID: {user_id}"
        )
    else:
        await message.answer("❌ Вы не зарегистрированы. Нажмите /start")


@dp.message(F.text == "📱 Мой ID")
async def show_id(message: Message):
    """Показывает ID пользователя"""
    await message.answer(f"🆔 Ваш Telegram ID: {message.from_user.id}")


@dp.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    """Показывает справку"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    help_text = "📖 **Справка по командам**\n\n"
    help_text += "**Для всех пользователей:**\n"
    help_text += "/start — Начать работу с ботом\n"
    help_text += "/balance — Проверить баланс\n\n"

    if user and user[5] in ['admin', 'superadmin']:
        help_text += "**Для админов:**\n"
        help_text += "/add {телефон} {сумма} — Начислить жетоны\n"
        help_text += "/sub {телефон} {сумма} — Вычесть жетоны\n"
        help_text += "/register {телефон} {имя} — Зарегистрировать вручную\n"
        help_text += "/delete {телефон} — Удалить пользователя\n"
        help_text += "/search {телефон} — Найти пользователя\n"
        help_text += "/myusers — Список пользователей\n\n"

    if user and user[5] == 'superadmin':
        help_text += "**Для главного админа:**\n"
        help_text += "/makeadmin {user_id} — Назначить админа\n"
        help_text += "/removeadmin {user_id} — Снять админа\n"
        help_text += "/admins — Список админов\n"
        help_text += "/setbalance {телефон} {сумма} — Установить баланс\n"
        help_text += "/stats — Статистика бота\n"
        help_text += "/broadcast {текст} — Рассылка всем\n"

    await message.answer(help_text, parse_mode="Markdown")


@dp.message(Command("balance"))
async def cmd_balance(message: Message):
    """Команда /balance"""
    await show_balance(message)


# ==================== КОМАНДЫ ДЛЯ АДМИНОВ ====================

@dp.message(Command("add"))
async def cmd_add(message: Message):
    """Начисление жетонов: /add {phone} {amount}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    # Проверка прав
    if not user or user[5] not in ['admin', 'superadmin']:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды")
        return

    # Парсим команду
    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Формат: /add {телефон} {сумма}\nПример: /add 79991234567 100")
        return

    phone = args[1]
    try:
        amount = int(args[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Сумма должна быть положительным числом")
        return

    # Ищем пользователя
    target_user = await get_user_by_phone(phone)
    if not target_user:
        await message.answer(f"❌ Пользователь с номером {phone} не найден")
        return

    # Начисляем
    target_user_id = target_user[0]
    target_name = target_user[2]
    await update_balance(target_user_id, amount)
    await log_transaction(user_id, target_user_id, amount, 'add')

    # Получаем новый баланс
    updated_user = await get_user(target_user_id)
    new_balance = updated_user[4]

    await message.answer(
        f"✅ Начислено {amount} жетонов\n"
        f"👤 Пользователь: {target_name}\n"
        f"📱 Телефон: {phone}\n"
        f"💰 Новый баланс: {new_balance} жетонов"
    )

    logger.info(f"Админ {user_id} начислил {amount} жетонов пользователю {target_user_id}")


@dp.message(Command("sub"))
async def cmd_sub(message: Message):
    """Вычитание жетонов: /sub {phone} {amount}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] not in ['admin', 'superadmin']:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Формат: /sub {телефон} {сумма}\nПример: /sub 79991234567 50")
        return

    phone = args[1]
    try:
        amount = int(args[2])
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Сумма должна быть положительным числом")
        return

    target_user = await get_user_by_phone(phone)
    if not target_user:
        await message.answer(f"❌ Пользователь с номером {phone} не найден")
        return

    target_user_id = target_user[0]
    target_name = target_user[2]
    await update_balance(target_user_id, -amount)
    await log_transaction(user_id, target_user_id, -amount, 'sub')

    updated_user = await get_user(target_user_id)
    new_balance = updated_user[4]

    await message.answer(
        f"✅ Вычтено {amount} жетонов\n"
        f"👤 Пользователь: {target_name}\n"
        f"💰 Новый баланс: {new_balance} жетонов"
    )


@dp.message(Command("register"))
async def cmd_register_manual(message: Message):
    """Ручная регистрация: /register {phone} {name}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] not in ['admin', 'superadmin']:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды")
        return

    args = message.text.split(maxsplit=2)
    if len(args) != 3:
        await message.answer("❌ Формат: /register {телефон} {имя}\nПример: /register 79991234567 Иван")
        return

    phone = args[1]
    name = args[2]

    existing = await get_user_by_phone(phone)
    if existing:
        await message.answer(f"❌ Пользователь с номером {phone} уже зарегистрирован")
        return

    await register_user(0, "", name, phone)

    await message.answer(
        f"✅ Пользователь зарегистрирован\n"
        f"👤 Имя: {name}\n"
        f"📱 Телефон: {phone}\n"
        f"💰 Баланс: 0 жетонов"
    )


@dp.message(Command("delete"))
async def cmd_delete(message: Message):
    """Удаление пользователя: /delete {phone}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] not in ['admin', 'superadmin']:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Формат: /delete {телефон}\nПример: /delete 79991234567")
        return

    phone = args[1]
    target_user = await get_user_by_phone(phone)

    if not target_user:
        await message.answer(f"❌ Пользователь с номером {phone} не найден")
        return

    target_role = target_user[5]

    if target_role in ['admin', 'superadmin']:
        await message.answer("⛔️ Нельзя удалить администратора")
        return

    await delete_user(target_user[0])

    await message.answer(
        f"✅ Пользователь удален\n"
        f"📱 Телефон: {phone}"
    )


@dp.message(Command("search"))
async def cmd_search(message: Message):
    """Поиск пользователя: /search {phone}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] not in ['admin', 'superadmin']:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Формат: /search {телефон}\nПример: /search 79991234567")
        return

    phone = args[1]
    target_user = await get_user_by_phone(phone)

    if not target_user:
        await message.answer(f"❌ Пользователь с номером {phone} не найден")
        return

    await message.answer(
        f"👤 Пользователь найден\n\n"
        f"🆔 ID: {target_user[0]}\n"
        f"👤 Имя: {target_user[2]}\n"
        f"📱 Телефон: {target_user[3]}\n"
        f"💰 Баланс: {target_user[4]} жетонов\n"
        f"🔰 Роль: {target_user[5]}"
    )


@dp.message(F.text == "👥 Список пользователей")
@dp.message(Command("myusers"))
async def cmd_myusers(message: Message):
    """Список всех пользователей"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] not in ['admin', 'superadmin']:
        await message.answer("⛔️ У вас нет прав для выполнения этой команды")
        return

    users = await get_all_users()

    if not users:
        await message.answer("📭 Список пользователей пуст")
        return

    text = "👥 **Список пользователей**\n\n"
    for u in users[:20]:
        text += f"👤 {u[2]} | 📱 {u[3]} | 💰 {u[4]} | 🔰 {u[5]}\n"

    if len(users) > 20:
        text += f"\n... и еще {len(users) - 20} пользователей"

    await message.answer(text, parse_mode="Markdown")


# ==================== КОМАНДЫ ДЛЯ ГЛАВНОГО АДМИНА ====================

@dp.message(Command("makeadmin"))
async def cmd_makeadmin(message: Message):
    """Назначение админа: /makeadmin {user_id}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] != 'superadmin':
        await message.answer("⛔️ Только главный администратор может назначать админов")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Формат: /makeadmin {user_id}\nПример: /makeadmin 123456789")
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return

    target_user = await get_user(target_id)
    if not target_user:
        await message.answer(f"❌ Пользователь с ID {target_id} не найден")
        return

    if target_user[5] == 'superadmin':
        await message.answer("⛔️ Нельзя изменить роль главного админа")
        return

    await update_role(target_id, 'admin')

    await message.answer(
        f"✅ Пользователь назначен администратором\n"
        f"🆔 ID: {target_id}\n"
        f"👤 Имя: {target_user[2]}"
    )


@dp.message(Command("removeadmin"))
async def cmd_removeadmin(message: Message):
    """Снятие админа: /removeadmin {user_id}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] != 'superadmin':
        await message.answer("⛔️ Только главный администратор может снимать админов")
        return

    args = message.text.split()
    if len(args) != 2:
        await message.answer("❌ Формат: /removeadmin {user_id}")
        return

    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом")
        return

    target_user = await get_user(target_id)
    if not target_user:
        await message.answer(f"❌ Пользователь с ID {target_id} не найден")
        return

    if target_user[5] == 'superadmin':
        await message.answer("⛔️ Нельзя снять главного админа")
        return

    await update_role(target_id, 'user')

    await message.answer(
        f"✅ Пользователь снят с должности админа\n"
        f"🆔 ID: {target_id}"
    )


@dp.message(Command("admins"))
async def cmd_admins(message: Message):
    """Список админов"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] != 'superadmin':
        await message.answer("⛔️ Только главный администратор может просматривать список админов")
        return

    admins = await get_admins()

    if not admins:
        await message.answer("📭 Список админов пуст")
        return

    text = "🔰 **Список администраторов**\n\n"
    for a in admins:
        role_emoji = "👑" if a[5] == 'superadmin' else "🔰"
        text += f"{role_emoji} {a[2]} | 🆔 {a[0]} | 📱 {a[3]}\n"

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("setbalance"))
async def cmd_setbalance(message: Message):
    """Установка точного баланса: /setbalance {phone} {amount}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] != 'superadmin':
        await message.answer("⛔️ Только главный администратор может устанавливать баланс")
        return

    args = message.text.split()
    if len(args) != 3:
        await message.answer("❌ Формат: /setbalance {телефон} {сумма}")
        return

    phone = args[1]
    try:
        amount = int(args[2])
        if amount < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Сумма должна быть неотрицательным числом")
        return

    target_user = await get_user_by_phone(phone)
    if not target_user:
        await message.answer(f"❌ Пользователь с номером {phone} не найден")
        return

    await set_balance(target_user[0], amount)
    await log_transaction(user_id, target_user[0], amount, 'set')

    await message.answer(
        f"✅ Баланс установлен\n"
        f"📱 Телефон: {phone}\n"
        f"💰 Новый баланс: {amount} жетонов"
    )


@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    """Статистика бота"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] != 'superadmin':
        await message.answer("⛔️ Только главный администратор может просматривать статистику")
        return

    stats = await get_stats()

    await message.answer(
        f"📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {stats['total_users']}\n"
        f"🔰 Админов: {stats['total_admins']}\n"
        f"💰 Сумма всех балансов: {stats['total_balance']} жетонов",
        parse_mode="Markdown"
    )


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: Message):
    """Рассылка всем пользователям: /broadcast {текст}"""
    user_id = message.from_user.id
    user = await get_user(user_id)

    if not user or user[5] != 'superadmin':
        await message.answer("⛔️ Только главный администратор может делать рассылку")
        return

    text_to_send = message.text.replace("/broadcast ", "", 1)

    if not text_to_send:
        await message.answer("❌ Укажите текст для рассылки\nПример: /broadcast Привет всем!")
        return

    users = await get_all_users()
    sent = 0
    failed = 0

    for u in users:
        try:
            await bot.send_message(u[0], text_to_send)
            sent += 1
        except:
            failed += 1

    await message.answer(
        f"✅ Рассылка завершена\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}"
    )


# ==================== ЗАПУСК БОТА ====================

async def main():
    """Главная функция запуска бота"""
    await init_db()
    logger.info("База данных инициализирована")

    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен")