import telebot
from config import TOKEN
from extensions import CryptoConverter, APIException
import redis
import logging
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

red = redis.Redis(host='localhost', port=6379)
bot = telebot.TeleBot(TOKEN)

symbols = CryptoConverter.get_currencies()


@bot.message_handler(commands=['start'])
def handle_start_help(message: telebot.types.Message):
    text = f"HELLO, {message.chat.username}!\n" \
           "I'm ChatBot where You can convert currencies!\n\n" \
           "Insert currencies to exchange in following format (in one line): \n" \
           "<currency to get> " \
           "<currency to exchange> " \
           "<amount to get>\n\n" \
           "Example:\n\nEUR USD 1\n\n"
    bot.reply_to(message, text)
    inline_keyboards(message)


def inline_keyboards(message):
    list_of_commands = ['START', 'HELP', 'VALUES', 'POPULAR_CURRENCIES', 'TIMESERIES']
    button_list = []
    for command in list_of_commands:
        button_list.append(telebot.types.InlineKeyboardButton(command, callback_data='/'+command.lower()))
    reply_markup = telebot.types.InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    bot.send_message(chat_id=message.from_user.id, text="Menu:", reply_markup=reply_markup)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


@bot.callback_query_handler(func=lambda c: c.data)
def process_callback(callback_query: telebot.types.CallbackQuery):
    code = callback_query.data
    if code in ['/start', '/help']:
        text = f"HELLO, {callback_query.from_user.username}!\n" \
               "I'm ChatBot where You can convert currencies!\n\n" \
               "Insert currencies to exchange in following format (in one line): \n" \
               "<currency to get> " \
               "<currency to exchange> " \
               "<amount to get>\n\n" \
               "Example:\n\nEUR USD 1\n\n"
        bot.send_message(callback_query.from_user.id, text=text)
    if code == '/values':
        text = "Available currencies:\n\n"
        global symbols
        for symbol, info in symbols.items():
            text += symbol + f' - {info.get("description")}\n'
        if len(text) > 4095:
            for x in range(0, len(text), 4095):
                bot.send_message(callback_query.from_user.id, text=text[x:x + 4095])
        else:
            bot.send_message(callback_query.from_user.id, text)
    if code == '/timeseries':
        text = f"Insert dates to get timeseries data\n" \
               f"in following format (in one line):\n" \
               f"<date_from> <date_to> <currency quote> <currency base>\n\n" \
               f"Example:\n\n" \
               f"2023-02-01 2023-02-20 USD XAU\n"
        mesg = bot.send_message(callback_query.from_user.id, text)
        bot.register_next_step_handler(mesg, get_timeseries)
    if code == '/popular_currencies':
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
        # markup = telebot.types.InlineKeyboardMarkup()
        if len(red.keys()) == 0:
            bot.send_message(callback_query.from_user.id, "You have not used yet any.\nTry for example:\n")
            buttons = [telebot.types.KeyboardButton("EUR USD 1"), telebot.types.KeyboardButton("USD RUB 1")]
            markup.add(*buttons)
        if 0 < len(red.keys()) <= 6:
            buttons = [telebot.types.KeyboardButton(key.decode() + " 1") for key in red.keys()]
            markup.add(*buttons)
        if len(red.keys()) > 6:
            pairs = [(int((red.get(key).decode())), key.decode()) for key in red.keys()]
            pairs.sort(reverse=True)
            buttons = [telebot.types.KeyboardButton(pair[1] + " 1") for pair in pairs]
            markup.add(*buttons[:6])
        bot.send_message(callback_query.from_user.id, "Popular currencies", reply_markup=markup)
    inline_keyboards(callback_query)


def get_timeseries(message: telebot.types.Message):
    date_from, date_to, quote, base = message.text.split()
    data = CryptoConverter.get_timeseries(date_from, date_to, quote, base)
    df = pd.DataFrame(data=list(data.get('rates').values()))
    df.columns = [base]
    df["date"] = list(data.get('rates').keys())
    df["date"] = df.date.apply(pd.to_datetime)
    df.set_index('date', inplace=True)
    ax = df.plot(kind='line', use_index=True, title=f"{base}/{quote}", grid=True, legend=True)
    ax.figure.savefig('output.png')
    bot.send_photo(message.from_user.id, photo=open('output.png', 'rb'))


# @bot.message_handler(commands=["values"])
# def handle_values(message: telebot.types.Message):
#     text = "Available currencies:\n\n"
#     global symbols
#     for symbol, info in symbols.items():
#         text += symbol + f' - {info.get("description")}\n'
#     if len(text) > 4095:
#         for x in range(0, len(text), 4095):
#             mesg = bot.reply_to(message, text=text[x:x + 4095])
#     else:
#         mesg = bot.reply_to(message, text)
#     bot.send_message(message.from_user.id, text)
#     inline_keyboards(message)
#     #bot.register_next_step_handler(mesg, inline_keyboards())


# @bot.message_handler(commands=["timeseries_data"])
# def handle_values(message: telebot.types.Message):
#     text = f"Insert dates to get timeseries data\n" \
#            f"in following format (in one line):\n" \
#            f"<date_from> <date_to> <currency quote> <currency base>\n\n" \
#            f"Example:\n\n" \
#            f"2023-02-01 2023-02-20 USD XAU\n"
#     mesg = bot.send_message(message.from_user.id, text)
#     bot.register_next_step_handler(mesg, get_timeseries)


# @bot.message_handler(commands=["popular_currencies"])
# def get_popular_currencies(message: telebot.types.Message):
#     markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
#     # markup = telebot.types.InlineKeyboardMarkup()
#     if len(red.keys()) == 0:
#         bot.reply_to(message, "You have not used yet any.\nTry for example:\n")
#         buttons = [telebot.types.KeyboardButton("EUR USD 1"), telebot.types.KeyboardButton("USD RUB 1")]
#         markup.add(*buttons)
#     if 0 < len(red.keys()) <= 6:
#         buttons = [telebot.types.KeyboardButton(key.decode() + " 1") for key in red.keys()]
#         markup.add(*buttons)
#     if len(red.keys()) > 6:
#         pairs = [(int((red.get(key).decode())), key.decode()) for key in red.keys()]
#         pairs.sort(reverse=True)
#         buttons = [telebot.types.KeyboardButton(pair[1] + " 1") for pair in pairs]
#         markup.add(*buttons[:6])
#     bot.send_message(message.from_user.id, "Popular currencies", reply_markup=markup)
#     inline_keyboards(message)


@bot.message_handler(content_types=["text"])
def convert(message: telebot.types.Message):
    global symbols
    try:
        values = message.text.split()
        if len(values) != 3:
            raise APIException("Wrong parameters quantity.")
        quote, base, amount = values
        price = CryptoConverter.get_price(quote, base)
    except APIException as e:
        bot.reply_to(message, f"User mistake.\n{e}")
    except Exception as e:
        bot.reply_to(message, f"Wrong command. Unable to continue.\n{e}")
    else:
        text = f"Pricing {amount} " \
               f"{symbols.get(quote)['description']} ({quote}) in " \
               f"{symbols.get(base)['description']} ({base}) - {round(price * int(amount), 2)}"
        bot.send_message(message.chat.id, text)

        used_pairs = red.get(f"{quote} {base}")
        if not used_pairs:
            red.set(f"{quote} {base}", 1)
        else:
            red.set(f"{quote} {base}", int(used_pairs.decode()) + 1)


bot.polling(none_stop=True, interval=0)
