from json import JSONEncoder

class Player():
    """
    Represents a player
    """
    def __init__(self, item):
        details = item['player'] # this is the original dictionary

        self.playerid = details['id']
        self.displayName = details['commonName'] if details['commonName'] is not '' else details['lastName']
        self.position = details['position']
        self.rating = details['rating']
        self.details = details

        self.maxBuy = item['buy']
        self.sell = item['sell']
        self.bin = item['bin']

        try:
            self.enabled = item['enabled']
        except:
            self.enabled = 'yes'

class PlayerEncoder(JSONEncoder):
    def default(self, o):
        return {
            'buy' : o.maxBuy,
            'sell': o.sell,
            'bin' : o.bin,
            'enabled': o.enabled,
            'player' : o.details
        }
