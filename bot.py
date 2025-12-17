import logging
from datetime import datetime, timedelta
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== НАСТРОЙКИ ====================
# ВАШ ТОКЕН БОТА (уже вставлен)
BOT_TOKEN = "8535879878:AAHtNnNEar31QA5jQzOtgHpqp3j5h3orS_Y"

# ВАШ ID в Telegram (уже вставлен)
ADMIN_ID = 380079648

# Часовой пояс Москвы (UTC+3)
MOSCOW_TZ_OFFSET = 3

# Время напоминаний (по Москве)
REMINDER_1_HOUR = 10  # 10:00
REMINDER_2_HOUR = 18  # 18:00

# Даты адвента
ADVENT_START = datetime(2025, 12, 17).date()
ADVENT_END = datetime(2025, 12, 31).date()
# ==================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Создаем базу данных и таблицы"""
    conn = sqlite3.connect('advent_bot.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            last_reminder_day INTEGER DEFAULT 0
        )
    ''')
    
    # Таблица наград
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rewards (
            day INTEGER PRIMARY KEY,
            reward_text TEXT NOT NULL,
            reward_name TEXT NOT NULL
        )
    ''')
    
    # Таблица связей пользователь-награда
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            day INTEGER,
            opened INTEGER DEFAULT 0,
            activated INTEGER DEFAULT 0,
            open_date TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (day) REFERENCES rewards(day)
        )
    ''')
    
    # ЗАПОЛНЯЕМ НАГРАДЫ (то, что вы написали)
    rewards = [
        (17, '🎁 Награда за 17 декабря: Сертификат на выходной. Активируй его и можешь в любой момент пропасть из чата как админ и участник на целые сутки!', 'Сертификат на выходной'),
        (18, '🎁 Награда за 18 декабря: Сертификат на префикс. Можно поменять префикс себе или любому участнику чата на любой который захочешь на сутки.', 'Сертификат на префикс'),
        (19, '🎁 Награда за 19 декабря: Сертификат на ошибку. Официальное прощение одного серьезного косяка в будущем (непреднамеренного). Не будет ни выговоров, ни публичного позора.', 'Сертификат на ошибку'),
        (20, '🎁 Награда за 20 декабря: Сертификат на какащке. Отправлю тебе бутлег браслетик какащке с вб. Этот: 249489457', 'Сертификат на какащке'),
        (21, '🎁 Награда за 21 декабря: Сертификат на «Вето». Сертификат позволяет один раз сказать самую гадкую гадость любому участнику чата или мне и за это ничего не будет.', 'Сертификат на «Вето»'),
        (22, '🎁 Награда за 22 декабря: Сертификат на видео. Посмотрю видео или фильм который ты выберешь и дам тебе подробный комментарий и мое мнение по результату просмотра. До 3 часов.', 'Сертификат на видео'),
        (23, '🎁 Награда за 23 декабря: Сертификат на победу в споре. Можно предъявить в любой момент чтобы победить в споре со мной.', 'Сертификат на победу в споре'),
        (24, '🎁 Награда за 24 декабря: Сертификат на вкусное. Отправлю тебе любую вкусняшку котоую ты выберешь', 'Сертификат на вкусное'),
        (25, '🎁 Награда за 25 декабря: Сертификат на мут. Право замутить любого участника чата на 12 часов (даже меня).', 'Сертификат на мут'),
        (26, '🎁 Награда за 26 декабря: Сертификат на выбор. Позволю тебе выбрать интересное для тебя занятие и запущу стрим где буду делать это/играть в это. Минимум два часа.', 'Сертификат на выбор'),
        (27, '🎁 Награда за 27 декабря: Сертификат на мой дизайн. Сделаю тебе дизайн-проект на твой выбор, аватарку или просто какую-то картинку.', 'Сертификат на дизайн'),
        (28, '🎁 Награда за 28 декабря: Сертификат на кастомную реакцию. На 48 часов ставлю настройку бота, которая будет реагировать на сообщение со словом которое ты выберешь, реакцией которую ты выберешь.', 'Сертификат на кастомную реакцию'),
        (29, '🎁 Награда за 29 декабря: Сертификат на подвеску. Отправлю тебе стальную подвеску с моим дизайном. Да-да, ту самую. Хайповая и стильная штука для крутых чувачков.', 'Сертификат на подвеску'),
        (30, '🎁 Награда за 30 декабря: Сертификат на «Карт-бланш». Полное разрешение сделать какую угодно манипуляцию с участником чата, типа мут, бан, префикс, разбан и тд.', 'Сертификат на «Карт-бланш»'),
        (31, '🎁 Награда за 31 декабря: Сертификат на желание. Да, желание - это нечто неощутимое и размытое. Но я решил специально не вносить конкретики, чтобы у тебя была возможность загадать желание которое я постараюсь выполнить (в пределеах разумного). С новым годом!', 'Сертификат на желание')
    ]
    
    cursor.executemany('INSERT OR IGNORE INTO rewards (day, reward_text, reward_name) VALUES (?, ?, ?)', rewards)
    
    print("🔴 ПРОВЕРКА БАЗЫ ДАННЫХ НАЧАЛАСЬ:")
    
    # 1. Проверяем сколько записей в таблице rewards (используем индекс 0)
    cursor.execute('SELECT COUNT(*) FROM rewards')
    result = cursor.fetchone()
    print(f"🔴 В таблице rewards записей: {result[0]}")
    
    # 2. Выводим ВСЕ награды из базы (используем индексы 0 и 1)
    cursor.execute('SELECT day, reward_name FROM rewards ORDER BY day')
    all_rewards = cursor.fetchall()
    print("🔴 Полный список наград в базе:")
    for r in all_rewards:
        print(f"  День {r[0]}: {r[1]}")
    
    # 3. Проверяем, есть ли награда для дня 2 (текущего дня)
    cursor.execute('SELECT day, reward_name FROM rewards WHERE day = 2')
    day2_reward = cursor.fetchone()
    if day2_reward:
        print(f"🔴 Награда для дня 2 НАЙДЕНА: {day2_reward[1]}")
    else:
        print("🔴 КРИТИЧЕСКАЯ ОШИБКА: Награда для дня 2 НЕ НАЙДЕНА в базе!")
        print("🔴 Это значит, что таблица rewards заполнена только днями 17-31, а не 1-31")
    print("🔴 ПРОВЕРКА БАЗЫ ДАННЫХ ЗАВЕРШЕНА")
    # 🔴🔴🔴 КОНЕЦ БЛОКА ДЛЯ ВСТАВКИ 🔴🔴🔴
    
    conn.commit()
    conn.close()
    print("База данных создана и заполнена!")

def get_db_connection():
    """Подключаемся к базе данных"""
    conn = sqlite3.connect('advent_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================
def get_moscow_time():
    """Получаем текущее время по Москве"""
    return datetime.utcnow() + timedelta(hours=MOSCOW_TZ_OFFSET)

def get_current_advent_day():
    """Определяем текущий день адвента"""
    now_moscow = get_moscow_time()
    today = now_moscow.date()
    
    # Добавим логирование
    print(f"🔍 ДЕБАГ: сегодня {today}, ADVENT_START={ADVENT_START}, ADVENT_END={ADVENT_END}")
    
    if today < ADVENT_START:
        print(f"🔍 ДЕБАГ: сегодня раньше начала адвента, возвращаю None")
        return None
    if today > ADVENT_END:
        print(f"🔍 ДЕБАГ: сегодня позже конца адвента, возвращаю None")
        return None
    
    current_day = (today - ADVENT_START).days + 1
    print(f"🔍 ДЕБАГ: текущий день адвента: {current_day}")
    return current_day

def is_reward_opened_today(user_id):
    """Проверяем, открывал ли пользователь награду сегодня"""
    current_day = get_current_advent_day()
    if not current_day:
        print(f"🔴 ПРОВЕРКА is_reward_opened_today: current_day={current_day}, возвращаем False")
        return False
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM user_rewards WHERE user_id = ? AND day = ? AND opened = 1', (user_id, current_day))
    result = cursor.fetchone()
    conn.close()
    
    return result is not None

# ==================== КОМАНДЫ БОТА ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем команду /start"""
    user = update.effective_user
    
    # Регистрируем пользователя
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)',
                   (user.id, user.username, user.first_name, user.last_name))
    conn.commit()
    conn.close()
    
    # Создаем кнопки
    keyboard = [
        [InlineKeyboardButton("🎁 Открыть сегодняшнюю награду", callback_data='open_today')],
        [InlineKeyboardButton("📋 Мои открытые награды", callback_data='my_rewards')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Привет, {user.first_name}! 🎄\n"
        f"Добро пожаловать в Адвент-календарь!\n\n"
        f"Каждый день с 17 по 31 декабря ты можешь открывать новые награды.\n"
        f"Нажимай кнопку ниже, чтобы открыть сегодняшнюю награду!",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем нажатия на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'open_today':
        await open_today_reward(query)
    elif query.data == 'my_rewards':
        await show_my_rewards(query)
    elif query.data == 'back_to_main':
        await back_to_main_menu(query)
    elif query.data == 'activate_menu':
        await ask_reward_number(query)

async def open_today_reward(query):
    user_id = query.from_user.id
    current_day = get_current_advent_day()
    now_moscow = get_moscow_time()
    
    # Добавим логирование
    print(f"🔴 ДИАГНОСТИКА: user_id={user_id}, current_day={current_day}, now={now_moscow}")
    print(f"🔴 ДИАГНОСТИКА: ADVENT_START={ADVENT_START}, ADVENT_END={ADVENT_END}")
    
    # Проверяем период адвента
    if current_day is None:
        print(f"🔍 КНОПКА: current_day is None, выходим")
        if now_moscow.date() < ADVENT_START:
            await query.edit_message_text("🎅 Адвент-календарь еще не начался! Жди 17 декабря 2025 года!")
            return
        else:
            await query.edit_message_text("🎅 Адвент-календарь завершился! Спасибо за участие!")
            return
    
    # Проверяем, открывал ли уже сегодня
    print(f"🔴 ДИАГНОСТИКА: проверяем is_reward_opened_today...")
    if is_reward_opened_today(user_id):
        print(f"🔴 ДИАГНОСТИКА: пользователь УЖЕ открывал награду сегодня")
        next_day = now_moscow.replace(hour=0, minute=0, second=0) + timedelta(days=1)
        time_left = next_day - now_moscow
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        await query.edit_message_text(
            f"⏰ Сегодня ты уже открывал(а) награду!\n"
            f"Следующую можно открыть через {hours}ч {minutes}м",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📋 Мои награды", callback_data='my_rewards')]])
        )
        return

    print(f"🔴 ДИАГНОСТИКА: пользователь еще НЕ открывал награду, продолжаем...")
    print(f"🔴 ДИАГНОСТИКА: ПЕРЕД получением награды из БД")
    
    # Получаем награду за сегодня
    conn = get_db_connection()
    cursor = conn.cursor()
    print(f"🔴 ДИАГНОСТИКА: Подключились к БД, ищем награду day={current_day}")
    cursor.execute('SELECT reward_text, reward_name FROM rewards WHERE day = ?', (current_day,))
    reward = cursor.fetchone()
    print(f"🔴 ДИАГНОСТИКА: Результат поиска награды: {reward}")
    
    if reward:
        print(f"🔴 ДИАГНОСТИКА: Награда НАЙДЕНА: {reward['reward_name']}")
        
        # Сохраняем, что пользователь открыл награду
        cursor.execute('INSERT INTO user_rewards (user_id, day, opened, open_date) VALUES (?, ?, 1, ?)',
                      (user_id, current_day, now_moscow))
        conn.commit()
        print(f"🔴 ДИАГНОСТИКА: Запись добавлена в user_rewards")
        
        # Отправляем награду
        keyboard = [
            [InlineKeyboardButton("📋 Мои награды", callback_data='my_rewards')],
            [InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]
        ]
        
        await query.edit_message_text(
            text=f"🎉 Ура! Ты открыл(а) награду за {current_day} декабря!\n\n{reward['reward_text']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    else:
        # 🔴 ДОБАВЬТЕ ЭТУ СТРОКУ:
        print(f"🔴 ДИАГНОСТИКА: ОШИБКА! Награда НЕ НАЙДЕНА в таблице rewards для day={current_day}")
        
        # Сообщение об ошибке
        await query.edit_message_text(
            text=f"❌ Ошибка: награда за {current_day} декабря не найдена в базе данных!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')]])
        )
        conn.close()
        return
    
    conn.close()

async def show_my_rewards(query):
    """Показываем все открытые награды пользователя"""
    user_id = query.from_user.id
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Берем только открытые награды (как вы просили)
    cursor.execute('''
        SELECT r.day, r.reward_name, ur.activated
        FROM user_rewards ur
        JOIN rewards r ON ur.day = r.day
        WHERE ur.user_id = ? AND ur.opened = 1
        ORDER BY r.day
    ''', (user_id,))
    
    rewards = cursor.fetchall()
    conn.close()
    
    if not rewards:
        text = "📭 У тебя пока нет открытых наград.\nОткрывай награды каждый день с помощью кнопки «Открыть сегодняшнюю награду»!"
    else:
        text = "📋 Твои открытые награды:\n\n"
        for reward in rewards:
            if reward['activated']:
                text += f"✅ {reward['day']} декабря: {reward['reward_name']} (АКТИВИРОВАНА)\n"
            else:
                text += f"🎁 {reward['day']} декабря: {reward['reward_name']}\n"
        
        text += "\nЧтобы активировать награду, нажми кнопку ниже и введи номер дня (например: 17)"
    
    # Кнопки
    keyboard = []
    if rewards:
        keyboard.append([InlineKeyboardButton("🔢 Активировать награду", callback_data='activate_menu')])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data='back_to_main')])
    
    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def ask_reward_number(query):
    """Просим ввести номер награды для активации"""
    await query.edit_message_text(
        text="Введи номер награды (день декабря), которую хочешь активировать:\n\nНапример, для награды за 17 декабря введи: 17",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Назад", callback_data='my_rewards')]])
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем текстовые сообщения"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Проверяем, ввел ли пользователь число (для активации)
    if text.isdigit():
        day = int(text)
        
        if 17 <= day <= 31:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Проверяем, есть ли у пользователя эта награда и не активирована ли она
            cursor.execute('''
                SELECT ur.id, ur.activated, r.reward_name, u.first_name
                FROM user_rewards ur
                JOIN rewards r ON ur.day = r.day
                JOIN users u ON ur.user_id = u.user_id
                WHERE ur.user_id = ? AND ur.day = ? AND ur.opened = 1
            ''', (user_id, day))
            
            result = cursor.fetchone()
            
            if not result:
                await update.message.reply_text("❌ У тебя нет этой награды или ты ее еще не открыл(а)!")
            elif result['activated']:
                await update.message.reply_text("❌ Эта награда уже активирована!")
            else:
                # Активируем награду
                cursor.execute('UPDATE user_rewards SET activated = 1 WHERE id = ?', (result['id'],))
                
                # Отправляем уведомление админу (вам)
                try:
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=f"🎉 {result['first_name']} активировал(а) награду: \"{result['reward_name']}\""
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление админу: {e}")
                
                conn.commit()
                
                # Сообщение пользователю
                keyboard = [[InlineKeyboardButton("📋 Вернуться к наградам", callback_data='my_rewards')]]
                await update.message.reply_text(
                    f"✅ Награда \"{result['reward_name']}\" успешно активирована! Я получил уведомление!",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            
            conn.close()
            return
    
    # Если сообщение "Открыть"
    if text.lower() == 'открыть':
        current_day = get_current_advent_day()
        if current_day:
            # Проверяем, открывал ли уже
            if is_reward_opened_today(user_id):
                await update.message.reply_text("Сегодня ты уже открывал(а) награду! Возвращайся завтра!")
            else:
                # Создаем fake query для открытия
                class FakeQuery:
                    def __init__(self, user):
                        self.from_user = user
                        self.data = 'open_today'
                    async def answer(self): pass
                    async def edit_message_text(self, **kwargs):
                        await update.message.reply_text(**kwargs)
                
                fake_query = FakeQuery(update.effective_user)
                await open_today_reward(fake_query)
        else:
            await update.message.reply_text("Сейчас не время адвента!")
    else:
        await update.message.reply_text("Используй кнопки в меню для навигации! 🎄")

async def back_to_main_menu(query):
    """Возвращаемся в главное меню"""
    keyboard = [
        [InlineKeyboardButton("🎁 Открыть сегодняшнюю награду", callback_data='open_today')],
        [InlineKeyboardButton("📋 Мои открытые награды", callback_data='my_rewards')]
    ]
    
    await query.edit_message_text(
        text="Главное меню:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Отправляем напоминания"""
    now_moscow = get_moscow_time()
    current_day = get_current_advent_day()
    
    if not current_day:
        return
    
    current_hour = now_moscow.hour
    
    if current_hour in [REMINDER_1_HOUR, REMINDER_2_HOUR]:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Получаем всех пользователей
        cursor.execute('SELECT user_id, last_reminder_day FROM users')
        users = cursor.fetchall()
        
        for user in users:
            # Проверяем, не отправляли ли уже напоминание сегодня
            if user['last_reminder_day'] != current_day:
                # Проверяем, открыл ли пользователь сегодняшнюю награду
                if not is_reward_opened_today(user['user_id']):
                    try:
                        await context.bot.send_message(
                            chat_id=user['user_id'],
                            text=f"⏰ Напоминание! Не забудь открыть сегодняшнюю награду за {current_day} декабря! 🎁"
                        )
                        cursor.execute('UPDATE users SET last_reminder_day = ? WHERE user_id = ?',
                                     (current_day, user['user_id']))
                        conn.commit()
                    except Exception as e:
                        logger.error(f"Ошибка отправки напоминания: {e}")
        
        conn.close()

def main():
    """Основная функция"""
    # Создаем базу данных
    init_db()
    
    # Создаем приложение бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Настраиваем напоминания (каждые 30 минут проверяем)
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(send_reminders, interval=1800, first=10)
    
    # Запускаем бота
    print("Бот запущен! Нажми Ctrl+C для остановки.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':

    main()





