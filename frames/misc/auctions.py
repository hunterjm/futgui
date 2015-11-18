import tkinter.ttk as ttk
from enum import Enum

class EventType(Enum):
    SOLD = 1
    NEWBID = 2
    BIDWAR = 3
    BIN = 4
    BIDWON = 5
    LOST = 6
    OUTBID = 7
    UPDATE = 8

class Auctions():
    cards = {}

    def __init__(self, frame):
        t = ttk.Treeview(frame)
        t['columns'] = ('timestamp', 'initial bid', 'current bid', 'bin', 'expires')
        t.column("#0", width=75)
        t.column("timestamp",width=100)
        t.column("initial bid", width=50)
        t.column("current bid", width=50)
        t.column("bin", width=50)
        t.column("expires", width=50)

        t.heading("#0", text="Card name", anchor="w")
        t.heading("timestamp",text="timestamp")
        t.heading("initial bid", text="initial bid")
        t.heading("current bid", text="current bid")
        t.heading("bin", text="BIN")
        t.heading("expires", text="expires")

        t.tag_configure('won', foreground='#006400', background='grey')
        t.tag_configure('bid', foreground='#006400')
        t.tag_configure('war', foreground='#B77600')
        t.tag_configure('sold', foreground='#1C7CA9', background='grey')
        t.tag_configure('lost', foreground='#B70000', background='grey')

        self.view = t

    def get_view(self):
        return self.view

    def add_auction(self, card, timestamp, currbid, index='end', tag=''):
        if not card.cardid in self.cards:
            self.cards[card.cardid] = card
            return self.view.insert("", index, card.cardid, text=card.cardname, values=(timestamp, card.startingBid,
                                                                                        currbid, card.buyNowPrice,
                                                                                        card.expires), tags=(tag,))

    def update_status(self, card, timestamp, currbid, tag=''):
        if not card.cardid in self.cards:
            self.add_auction(card, timestamp, currbid, 'end', tag)
        else:
            options = self.view.item(card.cardid)
            options['values'] = (timestamp, card.startingBid,
                                 currbid, card.buyNowPrice,
                                 card.expires)
            if tag:
                options['tags'] = (tag,)
            self.view.item(card.cardid, text=options['text'], values=options['values'], tags=options['tags'])
        self.view.see(card.cardid)
        self.view.selection_set([card.cardid])

class Card():

    def __init__(self, item):
        self.cardid = item['id']
        self.resourceId = item['resourceId']
        self.tradeId = item['tradeId']
        self.cardType = item['itemType']
        self.buyNowPrice = item['buyNowPrice']
        self.startingBid = item['startingBid']
        self.currentBid = item['currentBid']
        self.contract = item['contract']
        self.expires = item['expires']

class PlayerCard(Card):

    def __init__(self, item, name):
        Card.__init__(self, item)
        self.cardname = name