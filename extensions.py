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

        URL = f"https://api.exchangerate.host/convert?from={quote}&to={base}"

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


if __name__ == "__main__":
    # pprint(Currency.get_all_currencies())
    price = CryptoConverter.get_price("USD", "R")
    print(price)
