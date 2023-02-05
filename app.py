import telebot
from config import TOKEN
from extensions import CryptoConverter, Currency, APIException
import redis


red = redis.Redis(host='localhost', port=6379)
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'help'])
def handle_help(message: telebot.types.Message):
    text = f"HELLO, {message.chat.username}!\n" \
           "I'm bot where You can convert currencies!\n\n" \
           "Insert currencies to exchange in following format (in one line): \n" \
           "<currency to get> " \
           "<currency to exchange> " \
           "<amount to get>\n\n" \
           "Example:\n\nEUR USD 1\n\n" \
           "/help - instructions.\n" \
           "/values - available currencies\n" \
           "/popular_currencies - 6 hottest queries"
    bot.reply_to(message, text)


@bot.message_handler(commands=["values"])
def handle_values(message: telebot.types.Message):
    text = "Available currencies:\n\n"
    for abbreviation, full_name in Currency.currencies.items():
        text += f' {abbreviation} - {full_name}\n'
    bot.reply_to(message, text)


@bot.message_handler(commands=["popular_currencies"])
def get_popular_currencies(message: telebot.types.Message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    if len(red.keys()) <= 6:
        buttons = [telebot.types.KeyboardButton(key.decode() + " 1") for key in red.keys()]
        markup.add(*buttons)
    if len(red.keys()) > 6:
        pairs = [(int((red.get(key).decode())), key.decode()) for key in red.keys()]
        pairs.sort(reverse=True)
        buttons = [telebot.types.KeyboardButton(pair[1] + " 1") for pair in pairs]
        markup.add(*buttons[:6])
    bot.send_message(message.from_user.id, "Popular currencies", reply_markup=markup)


@bot.message_handler(content_types=["text"])
def convert(message: telebot.types.Message):
    try:
        values = message.text.split()
        if len(values) != 3:
            raise APIException("Wrong parameters quantity.")
        quote, base, amount = values
        price = CryptoConverter.get_price(quote, base, amount)
    except APIException as e:
        bot.reply_to(message, f"User mistake.\n{e}")
    except Exception as e:
        bot.reply_to(message, f"Wrong command. Unable to continue.\n{e}")
    else:
        text = f"Pricing {amount} " \
               f"{Currency.currencies.get(quote)} ({quote}) in " \
               f"{Currency.currencies.get(base)} ({base}) - {round(price, 2)}"
        bot.send_message(message.chat.id, text)

        redis_data = red.get(f"{quote} {base}")
        if not redis_data:
            red.set(f"{quote} {base}", 1)
        else:
            red.set(f"{quote} {base}", int(redis_data.decode()) + 1)


bot.polling(none_stop=True, interval=0)
