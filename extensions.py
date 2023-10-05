import requests
import json
from exceptions import APIException, DataFrameException
from pprint import pprint
import re
import pandas as pd
import datetime
from tokens import EXCHANGERATE_HOST_API as API_KEY


def parse_message_text(values: str) -> str:
    if re.match("([A-Z]{3} ?){2}\d+", values):  # pattern 'USD RUB 1'
        return "exchange"
    elif re.match("(\d{4}-\d{2}-\d{2} ){2}([A-Z]{3} ?){2}", values):  # pattern '2022-10-05 2023-10-04 USD RUB'
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
    def get_price(quote: str, base: str) -> float:
        if quote == base:
            raise APIException(f"Impossible to exchange equal currencies ({quote.upper()} vs {base.upper()})")

        URL = (f"http://api.exchangerate.host/convert"
               f"?access_key={API_KEY}"
               f"&from={quote.upper()}"
               f"&to={base.upper()}"
               f"&amount=1")

        r = requests.get(URL)
        if r.status_code == 200:
            if json.loads(r.content).get("success"):
                return json.loads(r.content).get("result")
            else:
                raise APIException(json.loads(r.content).get("error").get("info"))
        else:
            raise APIException(json.loads(r.content)["message"])

    @staticmethod
    def get_currencies() -> dict:
        url = f'http://api.exchangerate.host/list?access_key={API_KEY}'
        response = requests.get(url)
        data = response.json()
        return data.get('currencies')

    @staticmethod
    def get_timeseries(date_from: str, date_to: str, quote: str, base: str = "USD") -> None:
        url = (f'http://api.exchangerate.host/timeframe'
               f'?access_key={API_KEY}'
               f"&currencies={','.join([base.upper(),quote.upper()])}"
               f'&start_date={date_from}'
               f'&end_date={date_to}'
               f'&source={base}')
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # pprint(data)
            if data.get('success'):
                if not all(data.get('quotes').values()):
                    msg = ("Invalid_source_currency. \n"
                           f"You have supplied an invalid Source Currency '{quote}'. \n"
                           f"[Example: source=EUR]")
                    raise APIException(msg)
                try:
                    df = pd.DataFrame(data=list(data.get('quotes').values()))
                    df.columns = [base]
                    df["date"] = list(data.get('quotes').keys())
                    df["date"] = df.date.apply(pd.to_datetime)
                    df.set_index('date', inplace=True)
                    ax = df.plot(kind='line', use_index=True, title=f"{base}/{quote}", grid=True, legend=True)
                    ax.figure.savefig('output.png')
                except Exception as e:
                    raise DataFrameException(e)
            else:
                raise APIException(data.get("error").get("type") + "\n" + data.get("error").get("info"))
        else:
            raise APIException(json.loads(response.content)["message"])


if __name__ == "__main__":
    # pprint(Currency.get_all_currencies())
    # price = CryptoConverter.get_price("USD", "RUB")
    res = CryptoConverter.get_timeseries('2023-10-01', '2023-10-05', 'USD', 'EUR')
    # pprint(list(time_series.get('rates').keys()))
    # pprint(list(time_series.get('rates').values()))
    # curr = CryptoConverter.get_all_currencies()
    # print(curr)
    # res = CryptoConverter.get_currencies()
    print(res)
    # pprint(price)
