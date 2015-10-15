import tkinter as tk
from frames.base import Base
import multiprocessing as mp
import queue
import time
from PIL import Image, ImageTk
from core.playercard import create
from core.watch import watch

class Watch(Base):
    def __init__(self, master, controller):
        Base.__init__(self, master, controller)

        self._job = None
        self._watching = False
        self._errorCount = 0
        self.q = mp.Queue()
        self.p = None

        options = tk.Frame(self, bg='#1d93ab')
        options.grid(column=0, row=0, sticky='ns')

        stats = tk.Frame(self, bg='#1d93ab')
        stats.grid(column=1, row=0)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        back = tk.Button(options, bg='#1d93ab', text='Back to Bidding', command=self.bid)
        back.grid(column=0, row=0, sticky='we')

        self.card = tk.Label(options, bg='#1d93ab')
        self.card.grid(column=0, row=1)

        descLbl = tk.Label(stats, text='We are watching all of the trades for the next 20 minutes, and reporting below:', bg='#1d93ab', fg='#ffeb7e')
        descLbl.grid(column=0, row=0, columnspan=2)
        watchLbl = tk.Label(stats, text='Watched Trades:', bg='#1d93ab', fg='#ffeb7e')
        watchLbl.grid(column=0, row=1, sticky='e')
        self.numwatch = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.numwatch.grid(column=1, row=1)
        activeLbl = tk.Label(stats, text='Active Trades:', bg='#1d93ab', fg='#ffeb7e')
        activeLbl.grid(column=0, row=2, sticky='e')
        self.numactive = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.numactive.grid(column=1, row=2)
        bidLbl = tk.Label(stats, text='Trades with a Bid:', bg='#1d93ab', fg='#ffeb7e')
        bidLbl.grid(column=0, row=3, sticky='e')
        self.numbid = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.numbid.grid(column=1, row=3)
        lowLbl = tk.Label(stats, text='Lowest Bid:', bg='#1d93ab', fg='#ffeb7e')
        lowLbl.grid(column=0, row=4, sticky='e')
        self.low = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.low.grid(column=1, row=4)
        midLbl = tk.Label(stats, text='Median Bid:', bg='#1d93ab', fg='#ffeb7e')
        midLbl.grid(column=0, row=5, sticky='e')
        self.mid = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.mid.grid(column=1, row=5)
        avgLbl = tk.Label(stats, text='Average Bid:', bg='#1d93ab', fg='#ffeb7e')
        avgLbl.grid(column=0, row=6, sticky='e')
        self.avg = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.avg.grid(column=1, row=6)
        lowUnsoldLbl = tk.Label(stats, text='Lowest UNSOLD List Price:', bg='#1d93ab', fg='#ffeb7e')
        lowUnsoldLbl.grid(column=0, row=7, sticky='e')
        self.lowUnsold = tk.Label(stats, text='0', bg='#1d93ab', fg='#ffeb7e')
        self.lowUnsold.grid(column=1, row=7)

        self.checkQueue()

    def watch(self):
        self.p = mp.Process(target=watch, args=(
            self.q,
            self.controller.api,
            int(self.args['player']['id'])
            ))
        self.p.start()

    def checkQueue(self):
        try:
            status = self.q.get(False)
            self.numwatch.config(text=status['total'])
            self.numactive.config(text=status['active'])
            self.numbid.config(text=status['bidding'])
            self.low.config(text=status['lowest'])
            self.mid.config(text=status['median'])
            self.avg.config(text=status['mean'])
            self.lowUnsold.config(text=status['minUnsoldList'])
            self.update_idletasks()
        except queue.Empty:
            pass
        finally:
            self.after(100, self.checkQueue)

    def bid(self):
        if self.p is not None:
            self.p.terminate()
        self.controller.show_frame(Bid, player=self.args['player'])

    def active(self):
        if self.controller.api is None:
            self.controller.show_frame(Login)

        Base.active(self)
        displayName = self.args['player']['commonName'] if self.args['player']['commonName'] is not '' else self.args['player']['lastName']
        self.controller.status.set_status('Watching auctions for %s...' % displayName)
        img = ImageTk.PhotoImage(create(self.args['player']))
        self.card.config(image=img)
        self.card.image = img
        self.numwatch.config(text='0')
        self.numactive.config(text='0')
        self.numbid.config(text='0')
        self.low.config(text='0')
        self.mid.config(text='0')
        self.avg.config(text='0')
        self.lowUnsold.config(text='0')
        self.update_idletasks()
        self.watch()

from frames.login import Login
from frames.bid import Bid
from fut.exceptions import FutError, PermissionDenied, ExpiredSession
from requests.exceptions import RequestException
