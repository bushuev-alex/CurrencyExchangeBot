import requests
import json
from exceptions import APIException
from pprint import pprint
import re
import pandas as pd
import datetime


def parse_message_text(values: str) -> str:
    if re.match("([A-Z]{3} ?){2}\d+", values):
        return "exchange"
    elif re.match("(\d{4}-\d{2}-\d{2} ){2}([A-Z]{3} ?){2}", values):
        return "timeseries"
    else:
        return "wrong_query"


class CryptoConverter:
    START_HELP_TEXT = "HELLO, {}!\n" \
                      f"I'm ChatBot where You can: \n" \
                      f"1. Convert currencies \n" \
                      f"2. Get timeseries data to currency pairs!\n\n" \
                      f"To get exchange rate: \nInsert currencies in following format (in one line): \n" \
                      f"<currency to get> " \
                      f"<currency to exchange> " \
                      f"<amount to get>\n\n" \
                      f"Example:\n\nEUR USD 1\n\n\n" \
                      f"To get graphic image with timeseries data: \n" \
                      f"Insert dates and currencies in following format (in one line):\n" \
                      f"<date_from> <date_to> <currency quote> <currency base>\n\n" \
                      f"Example:\n\n" \
                      f"{datetime.datetime.now().replace(year=datetime.datetime.now().year - 1).date()} " \
                      f"{datetime.datetime.now().date()} EUR USD\n"

    @staticmethod
    def get_price(quote: str, base: str):
        if quote == base:
            raise APIException(f"Impossible to exchange equal currencies ({quote.upper()} vs {base.upper()})")

        URL = f"https://api.exchangerate.host/convert?from={quote.upper()}&to={base.upper()}"  # popular_currencies

        r = requests.get(URL)
        print(json.loads(r.content))
        if r.status_code == 200:
            if json.loads(r.content).get("success"):
                return json.loads(r.content).get("result")
            else:
                raise APIException(json.loads(r.content)["error"]["info"])
        else:
            raise APIException(json.loads(r.content)["message"])

    @staticmethod
    def get_currencies() -> dict:
        url = 'https://api.exchangerate.host/symbols'
        response = requests.get(url)
        data = response.json()
        return data['symbols']

    # @staticmethod
    # def get_all_currencies() -> dict:
    #     URL = f"https://api.apilayer.com/currency_data/list"
    #     headers = {"apikey": APILAYER_API_KEY}
    #     r = requests.get(url=URL, headers=headers)
    #     if r.status_code == 200:
    #         if json.loads(r.content).get("success"):
    #             return json.loads(r.content).get("currencies")
    #         else:
    #             raise APIException(json.loads(r.content)["error"]["info"])
    #     else:
    #         raise APIException(json.loads(r.content)["message"])

    @staticmethod
    def get_timeseries(date_from: str, date_to: str, quote: str, base: str = "USD"):
        url = f'https://api.exchangerate.host/timeseries?' \
              f'base={base.upper()}&' \
              f'symbols={quote.upper()}&' \
              f'start_date={date_from}&' \
              f'end_date={date_to}'
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data=list(data.get('rates').values()))
        df.columns = [base]
        df["date"] = list(data.get('rates').keys())
        df["date"] = df.date.apply(pd.to_datetime)
        df.set_index('date', inplace=True)
        ax = df.plot(kind='line', use_index=True, title=f"{base}/{quote}", grid=True, legend=True)
        ax.figure.savefig('output.png')


if __name__ == "__main__":
    # pprint(Currency.get_all_currencies())
    price = CryptoConverter.get_price("aaaa", "RUB")
    # CryptoConverter.get_timeseries('2022-03-07', '2023-03-05', 'USD', 'XXX')
    # pprint(list(time_series.get('rates').keys()))
    # pprint(list(time_series.get('rates').values()))
    # curr = CryptoConverter.get_all_currencies()
    # print(curr)
