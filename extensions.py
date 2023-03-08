import requests
import json
from config import APILAYER_API_KEY
from exceptions import APIException
from pprint import pprint
import re
import pandas as pd


def parse_message_text(values: str) -> str:
    if re.match("([A-Z]{3} ?){2}\d+", values):
        return "exchange"
    elif re.match("(\d{4}-\d{2}-\d{2} ){2}([A-Z]{3} ?){2}", values):
        return "timeseries"
    else:
        return "wrong_query"


class CryptoConverter:

    def __init__(self):
        pass

    @staticmethod
    def get_price(quote: str, base: str):
        if quote == base:
            raise APIException(f"Impossible to exchange equal currencies ({quote.upper()} vs {base.upper()})")

        URL = f"https://api.exchangerate.host/convert?from={quote.upper()}&to={base.upper()}"  # popular_currencies

        r = requests.get(URL)
        # print(json.loads(r.content))
        if r.status_code == 200:
            if json.loads(r.content).get("success"):
                return json.loads(r.content).get("result")
            else:
                raise APIException(json.loads(r.content)["error"]["info"])
        else:
            raise APIException(json.loads(r.content)["message"])

    @staticmethod
    def get_currencies():
        url = 'https://api.exchangerate.host/symbols'
        response = requests.get(url)
        data = response.json()
        return data['symbols']


    @staticmethod
    def get_all_currencies():
        URL = f"https://api.apilayer.com/currency_data/list"
        headers = {"apikey": APILAYER_API_KEY}
        r = requests.get(url=URL, headers=headers)
        if r.status_code == 200:
            if json.loads(r.content).get("success"):
                return json.loads(r.content).get("currencies")
            else:
                raise APIException(json.loads(r.content)["error"]["info"])
        else:
            raise APIException(json.loads(r.content)["message"])


    @staticmethod
    def get_timeseries(date_from: str, date_to: str, quote: str, base: str = "USD"):
        url = f'https://api.exchangerate.host/timeseries?' \
              f'base={base.upper()}&' \
              f'symbols={quote.upper()}&' \
              f'start_date={date_from}&' \
              f'end_date={date_to}'
        response = requests.get(url)
        #print(response.status_code)
        data = response.json()
        pprint(data)
        #return data
        df = pd.DataFrame(data=list(data.get('rates').values()))
        df.columns = [base]
        df["date"] = list(data.get('rates').keys())
        df["date"] = df.date.apply(pd.to_datetime)
        df.set_index('date', inplace=True)
        ax = df.plot(kind='line', use_index=True, title=f"{base}/{quote}", grid=True, legend=True)
        ax.figure.savefig('output.png')



if __name__ == "__main__":
    # pprint(Currency.get_all_currencies())
    # price = CryptoConverter.get_price("USD", "RUB")
    CryptoConverter.get_timeseries('2052-03-07', '2023-03-05', 'USD', 'AUD')
    #pprint(list(time_series.get('rates').keys()))
    #pprint(list(time_series.get('rates').values()))



