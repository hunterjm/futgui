import fut
import requests
import random
from time import time, sleep

cookies_file = 'cookies.txt'

class DelayedCore(fut.Core):
    def __init__(self, email, passwd, secret_answer, platform='pc', code=None, emulate=None, debug=False, cookies=cookies_file):
        # Set initial delay
        self.delayInterval = 2
        self.delay = time()
        super(DelayedCore, self).__init__(email, passwd, secret_answer, platform, code, emulate, debug, cookies)

    def setRequestDelay(self, delay):
        self.delayInterval = delay

    def resetSession(self):
        cookies = self.r.cookies
        headers = self.r.headers
        self.r = requests.Session()
        self.r.cookies = cookies
        self.r.headers = headers

    def __request__(self, method, url, *args, **kwargs):
        """Prepares headers and sends request. Returns response as a json object."""
        # Rate Limit requests based on delay interval
        if self.delay > time():
            sleep(self.delay - time())
        self.delay = time() + (self.delayInterval * random.uniform(0.75, 1.25))
        return super(DelayedCore, self).__request__(method, url, *args, **kwargs)

    def bid(self, trade_id, bid):
        # no delay between getting trade info and bidding
        delayInterval = self.delayInterval
        self.delayInterval = 0
        try:
            result = super(DelayedCore, self).bid(trade_id, bid)
        except fut.exceptions.PermissionDenied as e:
            if e.code == '461':
                result = False
            raise
        self.delayInterval = delayInterval
        return result
