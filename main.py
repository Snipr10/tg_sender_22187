import time
from concurrent.futures import ThreadPoolExecutor
import logging

import schedule
from datetime import datetime

from telebot.apihelper import ApiTelegramException

from settings import bot_data, chart_id
import telebot

from utils import get_results, get_result_messages, update_time_zone

bot = telebot.TeleBot(bot_data)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, f'Бот рассылки из DB')


@bot.message_handler(commands=['posts'])
def send_posts(message):
    send_messages()


def send_messages():
    try:
        logging.info("start")
        for m in get_result_messages():
            try:
                # if (len(m[0]), len(m[1]), len(m[2])) > 4000:
                if len(m[0]) > 4000:
                    for x in range(0, len(m[0]), 4000):
                        send_message((m[0][x:x + 4000], m[1][x:x + 4000], m[2][x:x + 4000]))
                else:
                    send_message(m)
            except Exception as e:
                print(f"unable to send message {e}")
    except Exception as e:
        print(f"unable to send messages {e}")


def send_message(m, attempt=0):
    if attempt > 3:
        try:
            bot.send_message(chart_id, m[2])
        except Exception as e:
            pass
        return
    try:
        bot.send_message(chart_id, m[0], parse_mode='HTML')
        return
    except ApiTelegramException as e:
        try:
            time.sleep(e.result_json['parameters']['retry_after'])
            send_message(m, attempt + 1)
        except Exception as e:
            print(e, attempt)
            try:
                bot.send_message(chart_id, m[1], parse_mode='Markdown')
                return
            except Exception as e:
                print(e, attempt)
                send_message(m, attempt + 1)
            logging.error(f"unable to send messages")
    except Exception as e:
        print(e, attempt)
        logging.error(f"unable to send messages {e}")
        send_message(m, attempt + 1)


schedule.every(3).minutes.do(send_messages)


def start_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)


def start_sending_message():
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except Exception as e:
            logging.info(e)


# logging.info(f"start_bot {update_time_zone(datetime.now())}")
print(f"start_bot {update_time_zone(datetime.now())}")

pool_source = ThreadPoolExecutor(3)
pool_source.submit(start_sending_message)
pool_source.submit(start_bot)
pool_source.shutdown()
