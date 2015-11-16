import tkinter.ttk as ttk
from enum import Enum

class EventType(Enum):
    SELL = 1
    NEWBID = 2
    BIDWAR = 3
    BIN = 4
    BIDWON = 5
    LOST = 6
    OUTBID = 7

class Auctions():
    cards = {}

    def __init__(self, frame):
        t = ttk.Treeview(frame)
        t['columns'] = ('timestamp', 'initial bid', 'current bid', 'bin')
        t.column("timestamp",width=75)
        t.column("initial bid", width=50)
        t.column("current bid", width=50)
        t.column("bin", width=50)
        t.heading("#0", text="Card name", anchor="w")
        t.heading("initial bid", text="initial bid")
        t.heading("current bid", text="current bid")
        t.heading("bin", text="BIN")

        t.heading("timestamp",text="timestamp")
        t.heading("initial bid", text="initial bid")
        t.heading("current bid", text="current bid")
        t.heading("bin", text="BIN")

        t.tag_configure('won', foreground='#006400', background='grey')
        t.tag_configure('bid', foreground='#006400')
        t.tag_configure('war', foreground='#B77600')
        t.tag_configure('sold', foreground='#B77600', background='grey')
        t.tag_configure('lost', foreground='#B70000', background='grey')

        # t.insert("",0,"dir1",text="directory 1")
        # t.insert("dir1","end","dir 1",text="file 1 1",values=("file 1 A","file 1 B"))
        # t.insert("", "end", "Alonso", text="Alsd", values=("foo", "bar"))

        self.view = t

    def get_view(self):
        return self.view

    def add_auction(self, card, timestamp, currbid, index='end', tag=''):
        if not card.cardid in self.cards:
            self.cards[card.cardid] = card
            return self.view.insert("", index, card.cardid, text=card.cardname, values=(timestamp, card.startingBid, currbid, card.buyNowPrice), tags=(tag,))

    def update_status(self, card, timestamp, currbid, tag=''):
        if not card.cardid in self.cards:
            self.add_auction(card, timestamp, currbid, 'end', tag)
        else:
            del self.cards[card.cardid]
            index = self.view.index(card.cardid)
            self.view.delete(card.cardid)
            self.add_auction(card, timestamp, currbid, index, tag)
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