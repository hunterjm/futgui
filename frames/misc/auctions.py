import tkinter as tk
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
    SELLING = 9

class Auctions():
    cards = {}

    def __init__(self, frame):
        self.view = tk.Frame(frame)
        self.view.grid_rowconfigure(0, weight=1)
        self.view.grid_columnconfigure(0, weight=1)
        self.view.grid_columnconfigure(1, weight=0)

        self.tree = ttk.Treeview(self.view, columns=('timestamp', 'initial', 'current', 'bin', 'expires'))
        self.tree.column("#0", width=75)
        self.tree.column("timestamp", width=100)
        self.tree.column("initial", width=50)
        self.tree.column("current", width=50)
        self.tree.column("bin", width=50)
        self.tree.column("expires", width=50)

        self.tree.heading("#0", text="Name", anchor="w")
        self.tree.heading("timestamp", text="Time")
        self.tree.heading("initial", text="Initial Bid")
        self.tree.heading("current", text="Current Bid")
        self.tree.heading("bin", text="BIN")
        self.tree.heading("expires", text="Expires")

        self.tree.tag_configure('bid', foreground='#006400')
        self.tree.tag_configure('war', foreground='#B77600')
        self.tree.tag_configure('selling', foreground='#1C7CA9')
        self.tree.tag_configure('lost', foreground='#B70000', background='grey')
        self.tree.tag_configure('won', foreground='#006400', background='grey')
        self.tree.tag_configure('sold', foreground='#1C7CA9', background='grey')

        # scrollbar
        ysb = ttk.Scrollbar(self.view, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=ysb.set)
        self.tree.grid(row=0, column=0, sticky='news')
        ysb.grid(row=0, column=1, sticky='ns')

    def get_view(self):
        return self.view

    def add_auction(self, card, timestamp, currbid, index='end', tag=''):
        if not card.cardid in self.cards:
            self.cards[card.cardid] = card
            return self.tree.insert("", index, card.cardid, text=card.cardname, values=(timestamp, card.startingBid,
                                                                                        currbid, card.buyNowPrice,
                                                                                        card.expires), tags=(tag,))

    def update_status(self, card, timestamp, currbid, tag=''):
        if not card.cardid in self.cards:
            self.add_auction(card, timestamp, currbid, 'end', tag)
        else:
            options = self.tree.item(card.cardid)
            options['values'] = (timestamp, card.startingBid,
                                 currbid, card.buyNowPrice,
                                 card.expires)
            if tag:
                options['tags'] = (tag,)
            self.tree.item(card.cardid, text=options['text'], values=options['values'], tags=options['tags'])
        self.tree.see(card.cardid)
        self.tree.selection_set([card.cardid])

class Card():

    def __init__(self, item):
        self.cardid = item['id']
        self.resourceId = item['resourceId']
        self.tradeId = item['tradeId']
        self.buyNowPrice = item['buyNowPrice'] if item['buyNowPrice'] is not None else item['lastSalePrice']
        self.startingBid = item['startingBid'] if item['startingBid'] is not None else "BIN"
        self.currentBid = item['currentBid'] if item['currentBid'] is not None else item['lastSalePrice']
        self.expires = item['expires'] if item['expires'] is not None else -1

class PlayerCard(Card):

    def __init__(self, item, name):
        Card.__init__(self, item)
        self.cardname = name