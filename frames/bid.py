import tkinter as tk
from frames.base import Base
import queue
import time
from PIL import Image, ImageTk
from core.playercard import create
from core.bid import bid

class Bid(Base):
    def __init__(self, master, controller):
        Base.__init__(self, master, controller)

        self._job = None
        self._bidding = False
        self._bidCycle = 0
        self._errorCount = 0

        options = tk.Frame(self, bg='#1d93ab')
        options.grid(column=0, row=0, sticky='ns')

        self.text = tk.Text(self, bg='#1d93ab', fg='#ffeb7e', bd=0)
        self.text.grid(column=1, row=0, sticky='news')
        self.q = queue.Queue()

        self.maxBid = tk.StringVar()
        self.sell = tk.StringVar()
        self.binPrice = tk.StringVar()
        self.minCredits = tk.StringVar()
        self.minCredits.set(1000)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        back = tk.Button(options, bg='#1d93ab', text='Back to Player Search', command=self.playersearch)
        back.grid(column=0, row=0, sticky='we')

        self.card = tk.Label(options, bg='#1d93ab')
        self.card.grid(column=0, row=1)

        form = tk.Frame(options, padx=15, pady=15)
        form.grid(column=0, row=2, sticky='ns')

        options.grid_columnconfigure(0, weight=1)
        options.grid_rowconfigure(0, weight=0)
        options.grid_rowconfigure(1, weight=0)
        options.grid_rowconfigure(2, weight=1)

        maxLbl = tk.Label(form, text='Max Bid:')
        maxLbl.grid(column=0, row=1, sticky='e')
        maxEntry = tk.Entry(form, width=8, textvariable=self.maxBid)
        maxEntry.grid(column=1, row=1, sticky='w')

        sellLbl = tk.Label(form, text='Sell For:')
        sellLbl.grid(column=0, row=2, sticky='e')
        sellEntry = tk.Entry(form, width=8, textvariable=self.sell)
        sellEntry.grid(column=1, row=2, sticky='w')

        binPriceLbl = tk.Label(form, text='BIN:')
        binPriceLbl.grid(column=0, row=3, sticky='e')
        binPriceEntry = tk.Entry(form, width=8, textvariable=self.binPrice)
        binPriceEntry.grid(column=1, row=3, sticky='w')

        minCreditsLbl = tk.Label(form, text='Min Credits:')
        minCreditsLbl.grid(column=0, row=4, sticky='e')
        minCreditsEntry = tk.Entry(form, width=8, textvariable=self.minCredits)
        minCreditsEntry.grid(column=1, row=4, sticky='w')

        self.bidbtn = tk.Button(form, text='Start Bidding', command=self.start)
        self.bidbtn.grid(column=0, row=5, columnspan=2, padx=5, pady=5)

        self.checkQueue()

    def bid(self):
        if not self._bidding:
            return
        # Populate trades with what I am already watching
        trades = {}
        try:
            for item in self.controller.api.watchlist():
                trades[item['tradeId']] = item['resourceId']
            self._bidding = True
            self._bidCycle += 1
            bid(
                self.q,
                self.controller.api,
                int(self.args['player']['id']),
                int(self.maxBid.get()),
                int(self.sell.get()),
                int(self.binPrice.get()),
                int(self.minCredits.get()),
                trades
                )
            self.controller.status.set_status('Bidding on %s: %d' % (self.displayName, self._bidCycle))
            self.controller.status.set_credits(self.controller.api.credits)
            self.after(5000, self.bid)
        except (PermissionDenied, ExpiredSession):
            self.stop()
            self.controller.show_frame(Login)
        except FutError as e:
            self.updateLog('%s    %s: %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), type(e).__name__, str(e)))
            self._errorCount += 1
            if(self._errorCount > 3):
                self.stop()
            pass

    def checkResult(self, r):
        self.updateLog('%s    Checking Result...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
        if r.ready():
            self.updateLog('%s    Result Success!\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
            self.bid()
        else:
            self.updateLog('%s    Still waiting...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
            self.after(500, self.checkResult, (r,))

    def start(self):
        if not self._bidding:
            self._bidding = True
            self._bidCycle = 0
            self._errorCount = 0
            self.bidbtn.config(text='STOP Bidding', command=self.stop)
            self.update_idletasks()
            self.updateLog('%s    Started bidding...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
            self.bid()

    def stop(self):
        if self._bidding:
            self._bidding = False
            self._bidCycle = 0
            self._errorCount = 0
            self.controller.status.set_status('Setting bid options for %s...' % self.displayName)
            self.bidbtn.config(text='Start Bidding', command=self.start)
            self.update_idletasks()
            self.updateLog('%s    Stopped bidding...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))

    def checkQueue(self):
        try:
            msg = self.q.get(timeout=0)
            self.updateLog(msg)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.checkQueue)

    def updateLog(self, msg):
        self.text.insert('end',msg)
        self.text.see(tk.END)
        self.update_idletasks()

    def playersearch(self):
        self.stop()
        self.controller.show_frame(PlayerSearch)

    def active(self):
        if self.controller.api is None:
            self.controller.show_frame(Login)

        Base.active(self)
        self.text.delete(1.0, tk.END)
        self.displayName = self.args['player']['commonName'] if self.args['player']['commonName'] is not '' else self.args['player']['lastName']
        self.text.insert(tk.END, '%s    Set Bid Options for %s...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), self.displayName))
        self.text.see(tk.END)
        img = ImageTk.PhotoImage(create(self.args['player']))
        self.card.config(image=img)
        self.card.image = img
        self.update_idletasks()

from frames.login import Login
from frames.playersearch import PlayerSearch
from fut.exceptions import FutError, PermissionDenied, ExpiredSession
