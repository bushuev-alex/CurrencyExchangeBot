import requests
import json
from config import APILAYER_API_KEY, OPENEXCHANGERATES_API
from pprint import pprint



class APIException(Exception):
    pass


class CryptoConverter:

    def __init__(self):
        pass

    @staticmethod
    def get_price(quote: str, base: str):
        if quote == base:
            raise APIException(f"Impossible to exchange equal currencies ({quote} vs {base})")

        URL = f"https://api.exchangerate.host/convert?from={quote}&to={base}"  # popular_currencies

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
              f'base={base}&' \
              f'symbols={quote}&' \
              f'start_date={date_from}&' \
              f'end_date={date_to}'
        response = requests.get(url)
        data = response.json()
        return data



if __name__ == "__main__":
    # pprint(Currency.get_all_currencies())
    # price = CryptoConverter.get_price("USD", "RUB")
    CryptoConverter.get_timeseries('2023-02-01', '2023-02-20', 'USD', 'XAU')
    #pprint(list(time_series.get('rates').keys()))
    #pprint(list(time_series.get('rates').values()))



