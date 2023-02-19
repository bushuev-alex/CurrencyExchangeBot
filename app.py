import telebot
from config import TOKEN
from extensions import CryptoConverter, APIException
import redis


red = redis.Redis(host='localhost', port=6379)
bot = telebot.TeleBot(TOKEN)

global symbols


@bot.message_handler(commands=['start', 'help'])
def handle_start_help(message: telebot.types.Message):
    global symbols
    symbols = CryptoConverter.get_currencies()
    text = f"HELLO, {message.chat.username}!\n" \
           "I'm ChatBot where You can convert currencies!\n\n" \
           "Insert currencies to exchange in following format (in one line): \n" \
           "<currency to get> " \
           "<currency to exchange> " \
           "<amount to get>\n\n" \
           "Example:\n\nEUR USD 1\n\n" \
           "/start or /help - instructions.\n" \
           "/values - available currencies\n" \
           "/popular_currencies - top 6 hottest pairs queries"
    bot.reply_to(message, text)

def small_helper(message: telebot.types.Message):
    text = f"/start or /help - instructions.\n" \
            "/values - available currencies\n" \
            "/popular_currencies - top 6 hottest pairs queries"
    bot.send_message(message.from_user.id, text)

@bot.message_handler(commands=["values"])
def handle_values(message: telebot.types.Message):
    text = "Available currencies:\n\n"
    global symbols
    for symbol, info in symbols.items():
        text += symbol + f' - {info.get("description")}\n'
    if len(text) > 4095:
        for x in range(0, len(text), 4095):
            bot.reply_to(message, text=text[x:x + 4095])
    else:
        bot.reply_to(message, text)
    small_helper(message)


@bot.message_handler(commands=["popular_currencies"])
def get_popular_currencies(message: telebot.types.Message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    # markup = telebot.types.InlineKeyboardMarkup()
    if len(red.keys()) == 0:
        bot.reply_to(message, "You have not used yet any.\nTry for example:\n")
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
    bot.send_message(message.from_user.id, "Popular currencies", reply_markup=markup)
    small_helper(message)


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
