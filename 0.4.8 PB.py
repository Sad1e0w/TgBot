import telebot
from telebot import types
import random
import logging
import sqlite3
from datetime import datetime


bot = telebot.TeleBot('7479421682:AAGlLfnR6maa6ZkPTkzHoXDAl0hfJW0sTQU')
OWNER_ID = 5782523765
OW_ID = '5782523765'
ignore_mode = False
logging.basicConfig(level=logging.INFO)

# Подключение к базе данных
conn = sqlite3.connect('dbODIN.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    registration_date DATETIME)''')
conn.commit()

# Обновленная таблица для сообщений с message_id
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    message_text TEXT,
                    chat_id INTEGER,
                    is_group BOOLEAN,
                    message_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

# Таблица для домашних заданий
cursor.execute('''CREATE TABLE IF NOT EXISTS homework (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    photo BLOB,
                    video BLOB,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY)''')

hw_data = {"text": "Домашнего задания нет.", "photo": None}
DEBUG = True

def log(message):
    if DEBUG: print(f"[DEBUG] {message}")

def is_ignored(user_id):
    return ignore_mode and str(user_id) != OW_ID
    
def is_admin(user_id):
    if user_id == OWNER_ID:
        return True
    cursor.execute('SELECT EXISTS(SELECT 1 FROM admins WHERE user_id=?)', (user_id,))
    return cursor.fetchone()[0] == 1

def save_message_to_db(message):
    if message.text:
        user_id = message.from_user.id
        username = message.from_user.username
        message_text = message.text
        chat_id = message.chat.id
        message_id = message.message_id
        is_group = chat_id < 0
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  
        try:
            cursor.execute('''
                INSERT INTO messages 
                (user_id, username, message_text, chat_id, is_group, message_id, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, message_text, chat_id, is_group, message_id, timestamp))
            conn.commit()
            logging.info(f"[{ 'Группа' if is_group else 'Лс'}] Сообщение от {message.from_user.username} - {message.text} |  {message_id} сохранено")
        except Exception as e:
            logging.error(f"Ошибка сохранения: {str(e)}")
            
@bot.message_handler(commands=['off'])
def ignore_handler(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/off' ")
    global ignore_mode
    if str(message.from_user.id) == OW_ID:
        ignore_mode = True
        bot.reply_to(message, "Бот в оффлайне.")
        log(f"Бот отключен ")
    else:
        log(f"Отказано в доступе")

@bot.message_handler(commands=['on'])
def unignore_handler(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/on' ")
    global ignore_mode
    if str(message.from_user.id) == OW_ID:
        ignore_mode = False
        bot.reply_to(message, "Бот в онлайне.")
        log(f"Бот включен")
    else:
        log(f"Отказано в доступе")

@bot.message_handler(commands=['sclear'])
def clear_message(message):
    try:
        # Удаление команды /clear сразу
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logging.error(f"Не удалось удалить команду: {str(e)}")

    if message.from_user.id != OWNER_ID:
        return  # Сообщение уже удалено, ничего не делаем
    
    if not message.reply_to_message:
        return  # Не реагируем на команду без ответа

    try:
        # Удаление из базы данных
        target_id = message.reply_to_message.message_id
        cursor.execute('DELETE FROM messages WHERE message_id = ?', (target_id,))
        conn.commit()
        
        # Удаление исходного сообщения
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        log(f"Удалено: {target_id}")
        
    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")

@bot.message_handler(commands=['clear'])
def clear_message(message):
    try:
        # Удаление команды /clear сразу
        bot.delete_message(message.chat.id, message.message_id)
    except Exception as e:
        logging.error(f"Не удалось удалить команду: {str(e)}")

    if message.from_user.id != OWNER_ID:
        return  # Сообщение уже удалено, ничего не делаем
    
    if not message.reply_to_message:
        return  # Не реагируем на команду без ответа

    try:
        # Удаление из базы данных
        target_id = message.reply_to_message.message_id
        cursor.execute('DELETE FROM messages WHERE message_id = ?', (target_id,))
        conn.commit()
        
        # Удаление исходного сообщения
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.send_message(message.chat.id, "Сообщение было удалено администратором")
        log(f"Удалено: {target_id}")
        
    except Exception as e:
        logging.error(f"Ошибка: {str(e)}")
        
@bot.message_handler(commands=['staff'])
def staff_command(message):
    save_message_to_db(message)
    try:
        admins_list = []
        
        # Добавляем владельца
        cursor.execute('''SELECT username FROM users WHERE user_id = ?''', (OWNER_ID,))
        owner_data = cursor.fetchone()
        admins_list.append(f" Владелец: @{owner_data[0] if owner_data else 'N/A'}")

        # Добавляем администраторов
        cursor.execute('''
            SELECT users.username 
            FROM admins 
            JOIN users ON admins.user_id = users.user_id
        ''')
        for admin in cursor.fetchall():
            admins_list.append(f" Админ: @{admin[0] if admin[0] else 'N/A'}")

        response = "Состав администрации:\n" + "\n".join(admins_list)
        bot.send_message(message.chat.id, response)
        
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Ошибка при получении данных")
        logging.error(f"Ошибка /staff: {str(e)}")
        
        
@bot.message_handler(commands=['setadmin'])
def set_admin_command(message):
    save_message_to_db(message)
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "❌ Нет прав!")
        return
    bot.reply_to(message, "Введите @username или user_id пользователя:")
    bot.register_next_step_handler(message, process_set_admin)

def process_set_admin(message):
    try:
        input_data = message.text.strip().lstrip('@')  # Удаляем @ если есть
        
        # Пробуем найти user_id разными способами
        if input_data.isdigit():
            user_id = int(input_data)
        else:
            # Ищем в базе по username
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (input_data,))
            result = cursor.fetchone()
            if not result:
                raise ValueError("Пользователь не найден")
            user_id = result[0]

        # Проверка существования пользователя
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        if not cursor.fetchone():
            raise ValueError("Пользователь не зарегистрирован в боте")

        # Добавление в админы
        cursor.execute('INSERT INTO admins (user_id) VALUES (?)', (user_id,))
        conn.commit()
        
        # Получение username для ответа
        cursor.execute('SELECT username FROM users WHERE user_id = ?', (user_id,))
        username = cursor.fetchone()[0] or "N/A"
        
        bot.reply_to(message, f"@{username} ({user_id}) добавлен в администраторы")

    except sqlite3.IntegrityError:
        bot.reply_to(message, "⚠️ Этот пользователь уже администратор")
    except ValueError as ve:
        bot.reply_to(message, f" Ошибка: {str(ve)}")
    except Exception as e:
        bot.reply_to(message, "Критическая ошибка")
        logging.error(f"Ошибка в setadmin: {str(e)}")

@bot.message_handler(commands=['deladmin'])
def del_admin_command(message):
    save_message_to_db(message)
    if message.from_user.id != OWNER_ID:
        bot.reply_to(message, "Нет прав!")
        return
    bot.reply_to(message, "Введите @username или user_id администратора:")
    bot.register_next_step_handler(message, process_del_admin)

def process_del_admin(message):
    try:
        input_data = message.text.strip().lstrip('@')
        
        if input_data.isdigit():
            target_id = int(input_data)
        else:
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (input_data,))
            result = cursor.fetchone()
            if not result:
                raise ValueError("Пользователь не найден")
            target_id = result[0]

        if target_id == OWNER_ID:
            raise ValueError("Нельзя удалить владельца")

        cursor.execute('SELECT 1 FROM admins WHERE user_id = ?', (target_id,))
        if not cursor.fetchone():
            raise ValueError("Пользователь не является администратором")

        cursor.execute('DELETE FROM admins WHERE user_id = ?', (target_id,))
        conn.commit()

        cursor.execute('SELECT username FROM users WHERE user_id = ?', (target_id,))
        username = cursor.fetchone()[0] if cursor.fetchone() else "N/A"
        bot.reply_to(message, f" @{username} ({target_id}) удалён из администраторов")

    except ValueError as ve:
        bot.reply_to(message, f"⚠️ Ошибка: {str(ve)}")
    except Exception as e:
        bot.reply_to(message, "Критическая ошибка при удалении")
        logging.error(f"Ошибка в deladmin: {str(e)}")

@bot.message_handler(func=lambda message: is_ignored(message.from_user.id))
def ignore_all_handler(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    pass

@bot.message_handler(commands=['start'])
def start(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/start' ")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('Домашнее задание')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Учебники  Презентации')
    markup.row(btn2)
    btn3 = types.KeyboardButton('Ответы к экзаменам (( в тесте ))')
    btn4 = types.KeyboardButton('Конспекты')
    btn5 = types.KeyboardButton('Успеваемость (( в тесте ))')
    markup.row(btn3, btn4, btn5)
    bot.send_message(message.chat.id, "Приветствую, данный бот предназначен для студентов группы ИС 2.2", reply_markup=markup)
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        cursor.execute('INSERT INTO users (user_id, username, first_name, last_name, registration_date) VALUES (?, ?, ?, ?, ?)',
                      (user_id, username, first_name, last_name, registration_date))
        conn.commit()
        bot.send_message(message.chat.id, "Вы были добавлены в бд")
    except sqlite3.IntegrityError:
        log(f"челик уже был добавлен в бд > {message.from_user.id} | {message.from_user.username} <")

# Обработчик команды /profile
@bot.message_handler(commands=['profile'])
def profile_command(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    user_id = message.from_user.id
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    
    if user_data:
        response = (f"👤 Ваш профиль:\n"
                    f"ID: {user_data[1]}\n"
                    f"Username: @{user_data[2]}\n"
                    f"Имя: {user_data[3]}\n"
                    f"Фамилия: {user_data[4]}\n"
                    f"Дата регистрации: {user_data[5]}")
    else:
        response = "❌ Вы не зарегистрированы! Введите /start"
    
    bot.send_message(message.chat.id, response)

# Обработчик команды /stats (только для админов)
@bot.message_handler(commands=['stats'])
def stats_command(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    if is_admin(message.from_user.id):
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        bot.send_message(message.chat.id, f"📊 Всего пользователей: {count}")
    else:
        bot.send_message(message.chat.id, "⛔ У вас нет прав для этой команды")

@bot.message_handler(commands=['s'])
def gmain(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton('Домашнее задание')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Учебники  Презентации')
    markup.row(btn2)
    btn3 = types.KeyboardButton('Ответы к экзаменам (( в тесте ))')
    btn4 = types.KeyboardButton('Конспекты')
    btn5 = types.KeyboardButton('Успеваемость (( в тесте ))')
    markup.row(btn3, btn4, btn5)

@bot.message_handler(func=lambda m: m.text == "Домашнее задание")
def dz(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'дз' ")
    try:
        cursor.execute('''
            SELECT text, photo, video FROM homework
            ORDER BY created_at DESC
            LIMIT 1
        ''')
        hw = cursor.fetchone()

        if not hw:
            bot.send_message(message.chat.id, "Домашнего задания нет.")
            return

        text, photo, video = hw

        if photo:
            bot.send_photo(message.chat.id, photo, caption=text)
        elif video:
            bot.send_video(message.chat.id, video, caption=text)
        else:
            bot.send_message(message.chat.id, text)

    except Exception as e:
        bot.reply_to(message, "⚠️ Ошибка при отображении ДЗ")
        logging.error(f"Ошибка отображения: {str(e)}")

    return gmain(message)

@bot.message_handler(func=lambda message: message.text == "Учебники  Презентации")
def main(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Уч/\Пр' ")
    study_text = "Выберите предмет"
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button4 = types.KeyboardButton("Назад")
    btn5 = types.KeyboardButton("БД")
    btn6 = types.KeyboardButton("ТРПО")
    arh = types.KeyboardButton("Архив")
    markup.row(btn6, btn5)
    markup.add(arh)
    markup.add(button4)
    bot.send_message(message.chat.id, study_text, reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text == "Архив")
def arh(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Архив' ")
    study_text = "Выберите предмет"
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    button1 = types.KeyboardButton("История")
    button2 = types.KeyboardButton("Общество")
    button3 = types.KeyboardButton('Русский')
    button4 = types.KeyboardButton("Назад 🔙")
    markup.row(button1, button2, button3)
    markup.add(button4)
    bot.send_message(message.chat.id, study_text, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "Назад 🔙")
def send_history_info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Назад 2' ")
    return main(message)

#БД
@bot.message_handler(func=lambda message: message.text == "БД")
def send_history_info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'БД' ")    
    bot.send_message(message.chat.id, "https://disk.yandex.ru/d/93bAEjg72d1b6w")

# "История"
@bot.message_handler(func=lambda message: message.text == "История")
def send_history_info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'История' ")    
    bot.send_message(message.chat.id, "https://disk.yandex.ru/d/zASh-kt7xRfJTA")

@bot.message_handler(func=lambda message: message.text == "Общество")
def send_ob_info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Общество' ")
    bot.send_message(message.chat.id, "https://disk.yandex.ru/d/2CIWQqZpjbzgRg")

@bot.message_handler(func=lambda message: message.text == "ТРПО")
def send_ob_info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Общество' ")
    bot.send_message(message.chat.id, "Папки еще нет, но вы держитесь")

@bot.message_handler(func=lambda message: message.text == "Русский")
def send_ob_info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Русский' ")
    bot.send_message(message.chat.id, "https://disk.yandex.ru/d/GX2QtZUdtlCdMg")

@bot.message_handler(func=lambda message: message.text == "Ответы к экзаменам (( в тесте ))")
def go_back(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Ответы к экз' ")
    bot.send_message(message.chat.id, "Coming soon..")
    
@bot.message_handler(func=lambda message: message.text == "Конспекты")
def cons(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Конспекты' ")
    hw = "Выберите дисциплину"
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    bt1 = types.KeyboardButton('БЖ')
    bt2 = types.KeyboardButton("Дисмат")
    back = types.KeyboardButton('Назад')
    markup.row(bt1, bt2)
    markup.add(back)
    bot.send_message(message.chat.id, hw, reply_markup=markup)
    
@bot.message_handler(func=lambda message: message.text == "БЖ")
def consd(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'БЖ' ")
    bot.send_message(message.chat.id, "https://disk.yandex.ru/d/-KP_xajf8OSxgg")
    
@bot.message_handler(func=lambda message: message.text == "Дисмат")
def consd(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Дисмат' ")    
    bot.send_message(message.chat.id, "https://disk.yandex.ru/d/jUjQ6S2KmPKlbQ")

@bot.message_handler(func=lambda message: message.text == "Успеваемость (( в тесте ))")
def go_back(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Успеваемость' ")
    bot.send_message(message.chat.id, "Coming soon..")

@bot.message_handler(func=lambda message: message.text == "Назад")
def go_back(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < использовал кнопку 'Назад' ")
    welcome_text = "Выберите одно из следующих действий:"
    markup = types.ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    btn1 = types.KeyboardButton('Домашнее задание')
    markup.row(btn1)
    btn2 = types.KeyboardButton('Учебники  Презентации')
    markup.row(btn2)
    btn3 = types.KeyboardButton('Ответы к экзаменам (( в тесте ))')
    btn4 = types.KeyboardButton('Конспекты')
    btn5 = types.KeyboardButton('Успеваемость (( в тесте ))')
    markup.row(btn3, btn4, btn5)
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.message_handler(commands=['id'])
def id(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/id' ")
    bot.reply_to(message, f'ID: {message.from_user.id}')

@bot.message_handler(func=lambda message: message.text == "/del")
def send_greeting(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/del' ")
    bot.send_message(message.chat.id, "Кнопки убраны", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(commands=['report'])
def start_report(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/report' ")
    bot.send_message(message.chat.id, "Пожалуйста, опишите вашу проблему.")
    bot.register_next_step_handler(message, process_report)

def process_report(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    user_id = message.from_user.username or message.from_user.first_name
    report_text = message.text
    report_message = f"Пользователь @{user_id} | {message.from_user.username} сообщил:{report_text}"
    bot.send_message(OWNER_ID, report_message)
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < отправил репорт. Содержание: {report_text} ")
    bot.send_message(message.chat.id, "Ваше сообщение отправлено администратору бота.")

@bot.message_handler(commands=['try'])
def flip_coin(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/try' ")
    result = random.choice(['Орел', 'Решка'])
    log(f"Результат подбрасывания: {result} ")
    bot.reply_to(message, f'Результат подбрасывания монетки: {result}')

@bot.message_handler(commands=['rek'])
def send_message_to_groups(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "Введите текст для рассылки в группы:")
        bot.register_next_step_handler(message, send_to_groups)
    else:
        bot.send_message(message.chat.id, "У вас нет прав на использование этой команды.")

def send_to_groups(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    text_to_send = message.text
    group_chat_ids = [-1002039534135]  
    for chat_id in group_chat_ids:
        try:
            bot.send_message(chat_id, text_to_send)
        except Exception as e:
            print(f'Ошибка при отправке сообщения в группу {chat_id}: {e}')
    bot.send_message(message.chat.id, "Рассылка завершена.")
    
@bot.message_handler(commands=['rekis'])
def send_message_to_groupss(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"===== Обработчик команды '/rekis' =====")
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/rekis' ")
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "Введите текст для рассылки в группы:")
        bot.register_next_step_handler(message, send_to_groups)
        log(f"Команда выполняется...")
    else:
        log(f"Отказано в доступе")
        bot.send_message(message.chat.id, "У вас нет прав на использование этой команды.")

@bot.message_handler(commands=['reki'])
def send_message_to_groupsss(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"===== Обработчик команды '/rekis' =====")
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/rekis' ")
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "Введите текст для рассылки в группы:")
        bot.register_next_step_handler(message, send_to_groupsss)
        log(f"Команда выполняется...")
    else:
        log(f"Отказано в доступе")
        bot.send_message(message.chat.id, "У вас нет прав на использование этой команды.")

def send_to_groupsss(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Успешно")
    text_to_send = message.text
    group_chat_iids = [-4536330961]  #ID группы ст
    for chat_id in group_chat_iids:
        try:
            bot.send_message(chat_id, text_to_send)
        except Exception as e:
            log(f"Ошибка. Проверь ид группы и статус")
            print(f'Ошибка при отправке сообщения в группу {chat_id}: {e}')
    bot.send_message(message.chat.id, "Рассылка завершена.")

@bot.message_handler(commands=["sv"])
def set_varible_handler(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f'===== Обработка команды "/sv" ===== ')
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/sv' ")
    if not is_admin(message.from_user.id):
        log(f"Отказано в доступе")
        bot.reply_to(message, "Нет прав!")
        return
        
    msg = bot.reply_to(message, "📤 Отправьте текст с фото/видео (или только текст/медиа)")
    bot.register_next_step_handler(msg, process_homework)

def process_homework(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    try:
        text = message.caption or message.text or ""
        photo = None
        video = None

        if message.photo:
            file_id = message.photo[-1].file_id
            file_info = bot.get_file(file_id)
            photo = bot.download_file(file_info.file_path)
        
        elif message.video:
            file_id = message.video.file_id
            file_info = bot.get_file(file_id)
            video = bot.download_file(file_info.file_path)

        cursor.execute('''
            INSERT INTO homework (text, photo, video)
            VALUES (?, ?, ?)
        ''', (text, photo, video))
        conn.commit()

        response = "✅ Домашнее задание сохранено в БД:\n"
        if photo: response += "- Фото\n"
        if video: response += "- Видео\n"
        response += f"- Текст: {text}" if text else ""
        
        bot.reply_to(message, response)

    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")
        logging.error(f"Ошибка при сохранении ДЗ: {str(e)}")


@bot.message_handler(commands=["gv"])
def get_varible_handler(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ
    log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/gv' ")
    bot.reply_to(message, f'Текущее ДЗ: {bot_varible}')
    log(f"Команда выполнена")

@bot.message_handler()
def info(message):
    save_message_to_db(message)  # СОХРАНЕНИЕ ВСЕХ ОСТАЛЬНЫХ СООБЩЕНИЙ
    if message.text.lower() == 'бот':
        log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду 'бот' ")
        bot.send_message(message.chat.id, 'На месте')
    elif message.text.lower() == '/bot':
        log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/bot' ")
        bot.send_message(message.chat.id, 'На месте')
    elif message.text.lower() == "/ver":
        log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/ver' ")
        bot.send_message(message.chat.id, "0.4.8 PB")
    elif message.text.lower() == "/help":
        log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/help' ")
        bot.send_message(message.chat.id, """
        Список команд:
    /id - ваш ID
    /ver - версия бота
    /report - сообщить о проблеме
    /start - запускает бота
    /del - убирает кнопки
    /help - список команд
    /try - подбрасывает монетку
    /link - ссылки на все группы/каналы
    /staff - Сочтав адсинистрации
    
    	Список команд для администрации:
    /clear - Удалить сообщение
    /sv - Поменять значение "ДЗ"
    /rekis - Отправить сообщение в группу от имени бота
         """)
        
    elif message.text.lower() == "/link":
        log(f"Пользователь > {message.from_user.id} | {message.from_user.username} < ввел команду '/link' ")
        bot.send_message(message.chat.id, """Список групп:
     """ "Вопросы и ответы - [кликни](https://t.me/+X78qGNPHtys0YmRi)" """
     """ "Дети удочки - [кликни](https://t.me/+efsAmD1j-ExlOWNi)" """
     """ "ДЗ ИС-2.2 - [кликни](https://t.me/+yzB4QnnRyXhmYmVi)",
                     parse_mode='Markdown')
                              
if __name__ == '__main__':
    logging.info("Бот запущен")
    bot.polling(none_stop=True)
