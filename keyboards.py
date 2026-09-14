from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Главное меню для обычного пользователя
def get_user_menu():
    """Создает клавиатуру для обычного пользователя"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Мой баланс")],
            [KeyboardButton(text="📱 Мой ID")],
            [KeyboardButton(text="ℹ️ Помощь")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Главное меню для админа
def get_admin_menu():
    """Создает клавиатуру для админа"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Мой баланс")],
            [KeyboardButton(text="📱 Мой ID")],
            [KeyboardButton(text="ℹ️ Помощь")],
            [KeyboardButton(text="👥 Список пользователей")]
        ],
        resize_keyboard=True
    )
    return keyboard


# Кнопка для запроса контакта
def get_phone_keyboard():
    """Создает кнопку для запроса номера телефона"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Зарегистрироваться", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard