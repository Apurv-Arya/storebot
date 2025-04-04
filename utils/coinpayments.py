import time, hmac, hashlib, requests
from utils.config import COINPAYMENTS_API_KEY, COINPAYMENTS_API_SECRET

class CoinPaymentsAPI:
    def __init__(self):
        self.key = COINPAYMENTS_API_KEY
        self.secret = COINPAYMENTS_API_SECRET
        self.base_url = 'https://www.coinpayments.net/api.php'

    def _post(self, payload):
        payload['version'] = 1
        payload['key'] = self.key
        payload['format'] = 'json'
        headers = {
            'HMAC': hmac.new(
                self.secret.encode(),
                requests.compat.urlencode(payload).encode(),
                hashlib.sha512
            ).hexdigest()
        }
        response = requests.post(self.base_url, data=payload, headers=headers)
        return response.json()

    def create_transaction(self, amount, currency='USD', buyer_email='storebot@nowhere.com'):
        payload = {
            'cmd': 'create_transaction',
            'amount': amount,
            'currency1': 'USD',
            'currency2': currency,
            'buyer_email': buyer_email,
            'item_name': 'StoreBot Balance Top-Up'
        }
        return self._post(payload)
