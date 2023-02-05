import requests
import json
from config import APILAYER_API_KEY


class APIException(Exception):
    pass


class CryptoConverter:

    def __init__(self):
        pass

    @staticmethod
    def get_price(quote: str, base: str, amount: str):
        if quote == base:
            raise APIException(f"Impossible to exchange equal currencies ({quote} vs {base})")

        URL = f"https://api.apilayer.com/currency_data/convert?to={base}&from={quote}&amount={amount}"
        headers = {"apikey": APILAYER_API_KEY}

        r = requests.get(url=URL, headers=headers)
        if r.status_code == 200:
            if json.loads(r.content).get("success"):
                return json.loads(r.content).get("result")
            else:
                raise APIException(json.loads(r.content)["error"]["info"])
        else:
            raise APIException(json.loads(r.content)["message"])


if __name__ == "__main__":
    price = CryptoConverter.get_price("BNB", "RUB", "2")
    print(price)
