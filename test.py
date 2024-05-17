import asyncio

import psycopg
import datetime
from telethon.sync import TelegramClient
from telethon import events, types

# Рабочий акк ЙО
# api_id = "28989554"
# api_hash = "442c36c81e946edca1f3037167c51d3a"
# phone = "+79677534804"
# name = "yoadmin"
# process_table = "yoclient_table"
# chats_table = "yoclient_chats"
# chat_id = -1001297863492


# Данные для инициализации скрита
# Рабочий акк Кзн
api_id = "13045110"  # id приложения с оф.сайта телеграма
api_hash = "752e3efaaa10aa5e8002ecee84382a72"  # хэш приложения с оф. сайта телеграма
phone = "+79872101445"  # номер телефона клиента
name = "KZN_ITS"  # название приложения, может быть любым
process_table = "holyclient_table"  # таблица в БД с процессами
chats_table = "holyclient_chats"  # таблица в БД с активными чатами
chat_id = -1001297863492

# инициализация клиента
client = TelegramClient(name, api_id, api_hash).start(phone=phone)

# смайлы, использующиеся в приложении
smiles = {'exclamation': '\U00002757', 'heart': '\U00002764', 'crying face': '\U0001F62D',
          'partying face': '\U0001F973', 'thinking face': '\U0001F914', 'winking face': '\U0001F609'}

# инициализация связи с БД
db = psycopg.connect("dbname=ufanet user=ufanet password=ufanet host = 192.168.96.89 port=5432")
local_time = +3

# текущие активные сесси в оперативной памяти
RAM_sessions = {}


async def get_from_db(table: str, attribute: str, condition: str) -> str:
    '''Функция запроса данных с БД. Аналог функции SELECT на SQL
    Аргументы: таблица, необходимый атрибут, состояние'''
    with db.cursor() as cur:
        cur.execute("SELECT %s FROM %s WHERE %s" % (attribute, table, condition))
        information = cur.fetchone()
    db.commit()
    return information


async def insert_into_db(table: str, attribute: str, values: str):
    '''Функция вставки данных в БД. Аналог функции INSERT на SQL.
    Аргументы: таблица, атрибуты, значения'''
    with db.cursor() as cur:
        cur.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, attribute, values))
    db.commit()


async def update_db(table: str, extension: str, condition: str):
    '''Обновление данных в таблице. Аналог функции UPDATE на SQL.
    Аргументы: таблица, расширение, состояние'''
    with db.cursor() as cur:
        cur.execute("UPDATE %s SET %s WHERE %s" % (table, extension, condition))
    db.commit()


async def delete_string_db(table: str, extension: str):
    '''Удаление строки из таблицы. Аналог функции DELETE на SQL.
    Аргументы: таблица, расширение'''
    with db.cursor() as cur:
        cur.execute("DELETE FROM %s WHERE %s" % (table, extension))
    db.commit()


async def get_dialog(dialogs, user_id):
    '''Получение информации об активных диалогах'''
    async for dialog in dialogs:
        try:
            if dialog.message.peer_id.user_id == user_id:
                return dialog
        except AttributeError:
            continue
    return None


async def check_process_time(message, process_id):
    print('Работает корутина "check_process_time". Номер процесса %s. Время срабатывания: %s. tgID: %s' %
          (process_id, str(datetime.datetime.now()), str(message.peer_id)))
    '''Получение информации о времени, затраченного на процесс'''
    # id пользователя
    user_id = message.peer_id.user_id
    # Кол-во секунд для непрочитанного сообщения
    await asyncio.sleep(900)
    # парсинг 10 последних диалогов
    dialogs = client.iter_dialogs(limit=20)
    # получение информации о диалогах
    dialog = await get_dialog(dialogs, user_id)
    # открыт или закрыт диалог
    status, = await get_from_db(process_table, "executor", "process_id = %s" % process_id)
    # проверка открытого и непринятого процесса
    if dialog.unread_count and status is None:
        await client.send_message(entity=chat_id,
                                  message='%s Внимание инженеры, есть непринятый процесс %s под номером %s!' % (
                                      smiles['exclamation'] * 3, smiles['crying face'], process_id[0]))
    print('Корутина "check_process_time" успешно завершена. Номер процесса %s. Время завершения: %s. tgID: %s' %
          (process_id, str(datetime.datetime.now()), str(message.peer_id.user_id)))


@client.on(events.NewMessage(pattern='#НовыйПроцесс', incoming=True))
async def new_process(event):
    print('Работает корутина "new_process". Время срабатывания: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))
    '''Функция обработки входящего процесса'''
    # Действительно ли процесс прилетел в ЛС
    if isinstance(event.peer_id, types.PeerUser):
        user_id = str(event.peer_id.user_id)
        # Есть ли активный процесс с человеком. Провека наличия сессии в Оперативной памяти
        if user_id in RAM_sessions.keys():
            reply_message = await event.reply(
                '%s У вас есть активный диалог с ИТС, пожалуйста закройте его, чтобы начать новый!' % smiles[
                    'exclamation'])
            await client.send_read_acknowledge(entity=reply_message.peer_id.user_id, max_id=reply_message.id)
        else:
            # Если произошел программный сбой и нужно проверить, есть ли активная сессия в БД
            session = await get_from_db(chats_table, "status", "user_id = '%s'" % user_id)
            if session is not None:
                reply_message = await event.reply(
                    '%s У вас уже есть активный диалог с ИТС. Чтобы его закрыть напишите #ЗакрытьПроцесс!' % smiles[
                        'exclamation'])
                await client.send_read_acknowledge(entity=reply_message.peer_id.user_id, max_id=reply_message.id)
            else:
                RAM_sessions[user_id] = {'Сессия': True, 'Пауза': False}
                try:
                    date = str(
                        event.original_update.date.astimezone(
                            tz=datetime.timezone(datetime.timedelta(hours=local_time))))
                except AttributeError:
                    date = str(event.original_update.message.date.astimezone(
                        tz=datetime.timezone(datetime.timedelta(hours=local_time))))
                await insert_into_db(process_table, "user_id, start_time, active", "'%s', '%s', True" % (user_id, date))
                await insert_into_db(chats_table, "user_id, status", "'%s', 'active'" % user_id)
                process_id = await get_from_db(process_table, "process_id", "user_id = '%s' AND start_time = '%s'"
                                               % (user_id, date))
                reply_message = await event.reply("%s Создан новый процесс под номером: %s. "
                                                  "Ожидайте, свободный инженер скоро Вам ответит!"
                                                  % (smiles['exclamation'], process_id[0]))
                await check_process_time(reply_message, process_id)
    print('Корутина "new_process" успешно завершена. Время завершения: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))


@client.on(events.NewMessage(incoming=True))
async def not_process_message(event):
    print('Работает корутина "not_process_message". Время срабатывания: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))
    '''Функция обработки паразитных процессов'''
    try:
        # Действительно ли процесс прилетел в ЛС
        if isinstance(event.peer_id, types.PeerUser):
            user_id = str(event.peer_id.user_id)
            date = str(event.message.date.astimezone
                       (tz=datetime.timezone
                       (datetime.timedelta
                        (hours=local_time))))
            # Если произошел программный сбой и нужно проверить, есть ли активная сессия в БД
            if event.message.text.find("#НовыйПроцесс") == -1 and event.message.text.find("#ЗакрытьПроцесс") == -1:
                if user_id not in RAM_sessions.keys() and user_id != str(777000):
                    session = await get_from_db(chats_table, "status", "user_id = '%s'" % user_id)
                    if session is None:
                        reply_message = await event.reply("%s Чтобы создать процесс на ИТС напишите #НовыйПроцесс, "
                                                          "закрытие процессов происходит с помощью #ЗакрытьПроцесс. "
                                                          "Желательно, чтобы процессы закрывали ИТС. "
                                                          "Служба теперь работает исключительно по процессам!%s "
                                                          "Инженеры ИТС не могут создавать чаты!" % (
                                                              smiles['thinking face'],
                                                              smiles['winking face']))
                        await client.send_read_acknowledge(entity=reply_message.peer_id.user_id,
                                                           max_id=reply_message.id)
                    else:
                        active_pause = await get_from_db(chats_table, "pause", "user_id = '%s'" % user_id)
                        if active_pause is not False:
                            RAM_sessions[user_id] = {"Сессия": True, "Пауза": True}
                        else:
                            RAM_sessions[user_id] = {"Сессия": True, "Пауза": False}
                if user_id in RAM_sessions.keys():
                    if RAM_sessions[user_id]["Пауза"] is True:
                        await update_db(process_table,
                                        "took_time = '%s'" % date,
                                        "user_id = '%s' AND active = True" % user_id)
                        await update_db(chats_table, "pause = False", "user_id = '%s'" % user_id)
                        RAM_sessions[user_id]["Пауза"] = False
        elif isinstance(event.peer_id, types.PeerChat):
            await client.send_read_acknowledge(entity=event.message.peer_id.chat_id, max_id=event.message.id)
        elif isinstance(event.peer_id, types.PeerChannel):
            await client.send_read_acknowledge(entity=event.message.peer_id.channel_id, max_id=event.message.id)
    except ValueError:
        print('Произошла ошибка в функции "not_process_message".', event.peer_id, type(event.peer_id))
    print('Корутина "not_process_message" успешно завершена. Время завершения: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))


@client.on(events.NewMessage(outgoing=True))
async def enable_work_time(event):
    print('Работает корутина "enable_work_time". Время срабатывания: %s' % str(datetime.datetime.now()))
    '''Функция подсчета рабочего времени, затраченного на процесс'''
    try:
        # Действительно ли процесс прилетел в ЛС
        if isinstance(event.peer_id, types.PeerUser):
            user_id = str(event.peer_id.user_id)
            # Если произошел программный сбой и нужно проверить, есть ли активная сессия в БД
            if user_id not in RAM_sessions.keys():
                session = await get_from_db(chats_table, "status", "user_id = '%s'" % user_id)
                if session is not None:
                    active_pause = await get_from_db(chats_table, "pause", "user_id = '%s'" % user_id)
                    if active_pause is True:
                        RAM_sessions[user_id] = {"Сессия": True, "Пауза": True}
            if user_id in RAM_sessions.keys():
                if RAM_sessions[user_id]['Пауза'] is True:
                    date = str(event.message.date.astimezone
                               (tz=datetime.timezone
                               (datetime.timedelta
                                (hours=local_time))))
                    await update_db(process_table,
                                    "took_time = '%s'" % date,
                                    "user_id = '%s' AND active = True" % user_id)
                    RAM_sessions[user_id]['Пауза'] = False
    except AttributeError:
        print("Что то пошло не так")
    print('Корутина "not_process_message" успешно завершена. Время завершения: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))


@client.on(events.NewMessage(pattern='#Принял ', outgoing=True))
async def get_executor(event):
    print('Работает корутина "get_executor". Время срабатывания: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))
    '''Запись имени принявшего инженера в таблицу и проверка выполнения процесса'''
    # Действительно ли процесс прилетел в ЛС
    if isinstance(event.peer_id, types.PeerUser):
        user_id = str(event.peer_id.user_id)
        # Если произошел программный сбой и нужно проверить, есть ли активная сессия в БД
        if user_id not in RAM_sessions.keys():
            session = await get_from_db(chats_table, "status", "user_id = '%s'" % user_id)
            if session is not None:
                RAM_sessions[user_id] = {"Сессия": True, "Пауза": False}
            else:
                return await event.reply(
                    "%s Чтобы принять процесс, сначала его создайте. Коллега, напишите #НовыйПроцесс. "
                    "Инженеры ИТС не могут создавать процессы." % smiles['thinking face'])
        (executor,) = await get_from_db(chats_table, "executor", "user_id = '%s'" % user_id)
        if executor is not None:
            await event.reply("%s Процесс выполняется другим инженером ИТС" % smiles['exclamation'])
        else:
            words = event.message.text.split()
            number_of_words = len(words)
            if number_of_words > 1:
                executor = words[1]
                await update_db(process_table,
                                "executor = '%s'" % executor,
                                "user_id = '%s' AND active = True" % user_id)
                date = str(event.message.date.astimezone
                           (tz=datetime.timezone
                           (datetime.timedelta
                            (hours=local_time))))
                await update_db(process_table, "took_time = '%s'" % date, "user_id = '%s' AND active = True" % user_id)
                return await update_db(chats_table,
                                       "executor = '%s'" % executor,
                                       "user_id = '%s'" % user_id)
            await client.send_read_acknowledge(entity=event.message.from_id, max_id=event.message.id)
    print('Корутина "get_executor" успешно завершена. Время завершения: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))


@client.on(events.NewMessage(pattern="#Пауза", outgoing=True))
async def pause_process(event):
    print('Работает корутина "pause_process". Время срабатывания: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))
    '''Постановка процесса на паузу'''
    # Действительно ли процесс прилетел в ЛС
    if isinstance(event.peer_id, types.PeerUser):
        user_id = str(event.peer_id.user_id)
        # Если произошел программный сбой и нужно проверить, есть ли активная сессия в БД
        if user_id not in RAM_sessions.keys():
            session = await get_from_db(chats_table, "status", "user_id = '%s'" % user_id)
            if session is not None:
                RAM_sessions[user_id] = {"Сессия": True, "Пауза": True}
                await update_db(chats_table, "pause = True", "user_id = '%s'" % user_id)
            else:
                return await event.reply(
                    "%s Чтобы поставить на паузу процесс, сначала его нужно создать. Коллега, напишите #НовыйПроцесс. "
                    "Инженеры ИТС не могут создавать процессы." % smiles['thinking face'])
        else:
            took_time, = await get_from_db(process_table, "took_time", "user_id = '%s' AND active = True" % user_id)
            if took_time is None:
                return await event.reply(
                    "%s Чтобы поставить на процесс паузу, сначала его нужно принять!" % smiles['thinking face'])
            await update_db(chats_table, "pause = True", "user_id = '%s'" % user_id)
            RAM_sessions[user_id]["Пауза"] = True
            date = str(event.message.date.astimezone
                       (tz=datetime.timezone
                       (datetime.timedelta(hours=local_time))))
            await update_db(process_table,
                            "pause_time = '%s'" % date,
                            "user_id = '%s' AND active = True" % user_id)
            await update_db(process_table,
                            "work_time = work_time + pause_time-took_time",
                            "user_id = '%s' AND active = True" % user_id)
    print('Корутина "pause_process" успешно завершена. Время завершения: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))


@client.on(events.NewMessage(pattern="#ЗакрытьПроцесс", incoming=True, outgoing=True))
async def close_process(event):
    print('Работает корутина "close_process". Время срабатывания: %s. tgID: %s' %
          (str(datetime.datetime.now()), str(event.peer_id)))
    '''Закрытие процесса и проверка выполнения процесса'''
    if isinstance(event.peer_id, types.PeerUser):
        user_id = str(event.peer_id.user_id)
        try:
            date = str(event.original_update.date.astimezone
                       (tz=datetime.timezone
                       (datetime.timedelta
                        (hours=local_time))))
        except AttributeError:
            date = str(event.original_update.message.date.astimezone(
                tz=datetime.timezone(datetime.timedelta(hours=local_time))))
        words = event.message.text.split()
        # Если произошел программный сбой и нужно проверить, есть ли активная сессия в БД
        if user_id not in RAM_sessions.keys():
            session = await get_from_db(chats_table, "status", "user_id = '%s'" % user_id)
            if session is None:
                reply_message = await event.reply(
                    "%s Чтобы закрыть процесс, сначала нужно его создать!" % smiles['exclamation'])
                await client.send_read_acknowledge(entity=reply_message.peer_id.user_id, max_id=reply_message.id)
                return reply_message
        else:
            RAM_sessions.pop(user_id)
        await update_db(process_table,
                        "stop_time = '%s'" % date,
                        "user_id = '%s' AND active = True" % user_id)
        await delete_string_db(chats_table, "user_id = '%s'" % user_id)
        if len(words) > 1:
            process_type = ",process_type = '%s'" % words[1]
        else:
            process_type = " "
        await update_db(process_table,
                        "process_time = stop_time - start_time, "
                        "work_time = work_time + stop_time-took_time,"
                        "active = False %s" % process_type,
                        "user_id = '%s' AND active = True" % user_id)
        reply_message = await event.reply('%s Процесс закрыт!' % smiles['partying face'])
        await client.send_read_acknowledge(entity=reply_message.peer_id.user_id, max_id=reply_message.id)
        print('Корутина "close_process" успешно завершена. Время завершения: %s. tgID: %s' %
              (str(datetime.datetime.now()), str(event.peer_id)))
        return reply_message


client.run_until_disconnected()
