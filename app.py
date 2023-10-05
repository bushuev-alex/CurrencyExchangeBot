import telebot
from tokens import TELEG_TOKEN
from extensions import CryptoConverter, parse_message_text
from exceptions import APIException
import redis
import logging


# Enable logging
logging.basicConfig(filename='log.txt',
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

red = redis.Redis(host='localhost', port=6379)
bot = telebot.TeleBot(TELEG_TOKEN)

symbols: dict = CryptoConverter.get_currencies()


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message: telebot.types.Message):
    print(f"User {message.from_user.username} joined the bot")
    logger.info(f"User {message.from_user.username} joined the bot")
    text = CryptoConverter.START_HELP_TEXT.format(message.chat.username)
    bot.reply_to(message, text)
    inline_keyboards(message)


def inline_keyboards(message):
    list_of_commands = ['START', 'HELP', 'VALUES', 'MOST_USED_PAIRS']
    button_list = []
    for command in list_of_commands:
        button_list.append(telebot.types.InlineKeyboardButton(command, callback_data='/'+command.lower()))
    reply_markup = telebot.types.InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    bot.send_message(chat_id=message.from_user.id, text="Menu:", reply_markup=reply_markup)


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None) -> list:
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


@bot.callback_query_handler(func=lambda c: c.data)
def process_callback(callback_query: telebot.types.CallbackQuery):
    code = callback_query.data
    logger.info(f"{code} button is pressed by user {callback_query.from_user.username}")
    if code in ['/start', '/help']:
        text = CryptoConverter.START_HELP_TEXT.format(callback_query.from_user.username)
        bot.send_message(callback_query.from_user.id, text=text)
    if code == '/values':
        text = "Available currencies:\n\n"
        global symbols
        for symbol, info in symbols.items():
            text += symbol + ' - ' + info + '\n'
        if len(text) > 4095:
            for x in range(0, len(text), 4095):
                bot.send_message(callback_query.from_user.id, text=text[x:x + 4095])
        else:
            bot.send_message(callback_query.from_user.id, text)
    if code == '/most_used_pairs':
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
        bot.send_message(callback_query.from_user.id, "Popular exchange pairs", reply_markup=markup)
    logger.info(f"Answer is sent to user {callback_query.from_user.username}")
    inline_keyboards(callback_query)


@bot.message_handler(content_types=["text"])
def convert(message: telebot.types.Message):
    global symbols
    try:
        parse_result = parse_message_text(message.text.strip())
        logger.info(f"User {message.from_user.username} query message is: {message.text}, "
                    f"the parse result is {parse_result}")
        if parse_result == "wrong_query":
            logger.error(APIException("Wrong parameters."))
            raise APIException("Wrong parameters.")

        values = message.text.strip().split()
        if parse_result == "exchange":
            quote, base, amount = values
            logger.info(f"User {message.from_user.username} query to exchange: {quote} {base} {amount}")
            price = CryptoConverter.get_price(quote, base)
            text = f"Pricing {amount} " \
                   f"{symbols.get(quote)} ({quote}) in " \
                   f"{symbols.get(base)} ({base}) - {round(price * int(amount), 2)}"
            bot.send_message(message.chat.id, text)
            logger.info(f"Answer was sent to user {message.from_user.username}: {text}")
            used_pairs = red.get(f"{quote} {base}")
            if not used_pairs:
                red.set(f"{quote} {base}", 1)
            else:
                red.set(f"{quote} {base}", int(used_pairs.decode()) + 1)
            logger.info("Redis base is updated")
        if parse_result == "timeseries":
            date_from, date_to, quote, base = values
            logger.info(f"User {message.from_user.username} query to exchange: {date_from} {date_to} {quote} {base}")
            CryptoConverter.get_timeseries(date_from, date_to, quote, base)
            bot.send_photo(message.from_user.id, photo=open('output.png', 'rb'))
            logger.info(f"Image was sent to user {message.from_user.username}.")
            inline_keyboards(message)
    except APIException as e:
        logger.error(APIException(f"User mistake. {e}"))
        bot.reply_to(message, f"User mistake.\n{e}")
    except Exception as e:
        logger.error(APIException(f"Wrong command. Unable to continue. {e}"))
        bot.reply_to(message, f"Wrong command. Unable to continue.\n{e}")


bot.polling(none_stop=True, interval=0)
