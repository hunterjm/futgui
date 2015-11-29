import tkinter as tk
import tkinter.ttk as ttk
import multiprocessing as mp
import queue
import time
import json
import requests
import locale
import webbrowser
import core.constants as constants

from tkinter import messagebox
from frames.base import Base
from frames.misc.auctions import Auctions, Card, EventType
from core.bid import bid, increment, roundBid
from core.watch import lowestBin
from api.delayedcore import DelayedCore
from os.path import expanduser


locale.setlocale(locale.LC_ALL, '')


class Bid(Base):
    def __init__(self, master, controller):
        Base.__init__(self, master, controller)

        self._bidding = False
        self._bidCycle = 0
        self._errorCount = 0
        self._banWait = 0
        self._startTime = 0
        self._lastUpdate = 0
        self._lastDonate = 0
        self._updatedItems = []
        self.auctionsWon = 0
        self.sold = 0

        self.q = mp.Queue()
        self.p = None

        self.rpm = tk.StringVar()
        self.minCredits = tk.StringVar()
        self.maxPlayer = tk.StringVar()
        self.autoUpdate = tk.IntVar()
        self.buy = tk.StringVar()
        self.sell = tk.StringVar()
        self.bin = tk.StringVar()
        self.snipeOnly = tk.IntVar()
        self.relistAll = tk.IntVar()

        self.settings = {
            'rpm': 20,
            'minCredits': 1000,
            'maxPlayer': 20,
            'autoUpdate': 0,
            'buy': 0.9,
            'sell': 1,
            'bin': 1.25,
            'snipeOnly': 0,
            'relistAll': 1
        }

        # Search for settings
        try:
            with open(constants.SETTINGS_FILE, 'r') as f:
                self.settings.update(json.load(f))
        except:
            pass

        # do we have a donation in our settings
        if 'donate' in self.settings:
            self._lastDonate = self.settings['donate']

        # Set initial values
        self.rpm.set(self.settings['rpm'])
        self.minCredits.set(self.settings['minCredits'])
        self.maxPlayer.set(self.settings['maxPlayer'])
        self.autoUpdate.set(self.settings['autoUpdate'])
        self.buy.set(int(self.settings['buy']*100))
        self.sell.set(int(self.settings['sell']*100))
        self.bin.set(int(self.settings['bin']*100))
        self.snipeOnly.set(self.settings['snipeOnly'])
        self.relistAll.set(self.settings['relistAll'])

        # Setup traces
        self.rpm.trace('w', self.save_settings)
        self.minCredits.trace('w', self.save_settings)
        self.maxPlayer.trace('w', self.save_settings)
        self.autoUpdate.trace('w', self.save_settings)
        self.buy.trace('w', self.save_settings)
        self.sell.trace('w', self.save_settings)
        self.bin.trace('w', self.save_settings)
        self.snipeOnly.trace('w', self.save_settings)
        self.relistAll.trace('w', self.save_settings)

        # Setup GUI
        options = tk.Frame(self)
        options.grid(column=0, row=0, sticky='ns')

        auctions = tk.Frame(self)

        self.auctionStatus = Auctions(auctions)
        self.auctionStatus.get_view().grid(column=0, row=0, sticky='nsew')

        self.logView = tk.Text(auctions, bg='#1d93ab', fg='#ffeb7e', bd=0)
        self.logView.grid(column=0, row=1, sticky='nsew')

        auctions.grid(column=1, row=0, sticky='nsew')
        auctions.grid_rowconfigure(0, weight=3)
        auctions.grid_rowconfigure(1, weight=1)
        auctions.grid_columnconfigure(0, weight=1)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        back = tk.Button(options, bg='#1d93ab', text='Back to Player Search', command=self.playersearch)
        back.grid(column=0, row=0, sticky='we')

        self.tree = ttk.Treeview(options, columns=('buy', 'sell', 'bin'), selectmode='browse')
        self.tree.heading('#0', text='Name', anchor='w')
        self.tree.column('buy', width=50, anchor='center')
        self.tree.heading('buy', text='Max Bid')
        self.tree.column('sell', width=50, anchor='center')
        self.tree.heading('sell', text='Sell')
        self.tree.column('bin', width=50, anchor='center')
        self.tree.heading('bin', text='BIN')
        self.tree.grid(column=0, row=1, sticky='ns')

        form = tk.Frame(options, padx=15, pady=15)
        form.grid(column=0, row=2)

        options.grid_columnconfigure(0, weight=1)
        options.grid_rowconfigure(0, weight=0)
        options.grid_rowconfigure(1, weight=1)
        options.grid_rowconfigure(2, weight=0)

        settingsLbl = tk.Label(form, text='Settings', font=('KnulBold', 16))
        settingsLbl.grid(column=0, row=0, columnspan=2)

        rpmLbl = tk.Label(form, text='RPM:')
        rpmLbl.grid(column=0, row=1, sticky='e')
        rpmEntry = tk.Entry(form, width=8, textvariable=self.rpm)
        rpmEntry.grid(column=1, row=1, sticky='w')

        minCreditsLbl = tk.Label(form, text='Min $:')
        minCreditsLbl.grid(column=0, row=2, sticky='e')
        minCreditsEntry = tk.Entry(form, width=8, textvariable=self.minCredits)
        minCreditsEntry.grid(column=1, row=2, sticky='w')

        maxPlayerLbl = tk.Label(form, text='Max Cards:')
        maxPlayerLbl.grid(column=0, row=3, sticky='e')
        maxPlayerEntry = tk.Entry(form, width=8, textvariable=self.maxPlayer)
        maxPlayerEntry.grid(column=1, row=3, sticky='w')

        snipeOnlyLbl = tk.Label(form, text='BIN Snipe:')
        snipeOnlyLbl.grid(column=0, row=4, sticky='e')
        snipeOnlyCheckbox = tk.Checkbutton(form, variable=self.snipeOnly)
        snipeOnlyCheckbox.grid(column=1, row=4, sticky='w')

        pricingLbl = tk.Label(form, text='Pricing', font=('KnulBold', 16))
        pricingLbl.grid(column=2, row=0, columnspan=2)

        autoUpdateLbl = tk.Label(form, text='Auto Update:')
        autoUpdateLbl.grid(column=2, row=1, sticky='e')
        autoUpdateCheckbox = tk.Checkbutton(form, variable=self.autoUpdate)
        autoUpdateCheckbox.grid(column=3, row=1, sticky='w')

        autoBuyLbl = tk.Label(form, text='Auto Bid %:')
        autoBuyLbl.grid(column=2, row=2, sticky='e')
        autoBuyEntry = tk.Entry(form, width=4, textvariable=self.buy)
        autoBuyEntry.grid(column=3, row=2, sticky='w')

        autoSellLbl = tk.Label(form, text='Auto Sell %:')
        autoSellLbl.grid(column=2, row=3, sticky='e')
        autoSellEntry = tk.Entry(form, width=4, textvariable=self.sell)
        autoSellEntry.grid(column=3, row=3, sticky='w')

        autoBINLbl = tk.Label(form, text='Auto BIN %:')
        autoBINLbl.grid(column=2, row=4, sticky='e')
        autoBINEntry = tk.Entry(form, width=4, textvariable=self.bin)
        autoBINEntry.grid(column=3, row=4, sticky='w')

        relistAllLbl = tk.Label(form, text='Same Relist $:')
        relistAllLbl.grid(column=2, row=5, sticky='e')
        relistAllCheckbox = tk.Checkbutton(form, variable=self.relistAll)
        relistAllCheckbox.grid(column=3, row=5, sticky='w')

        self.bidbtn = tk.Button(form, text='Start Bidding', command=self.start)
        self.bidbtn.grid(column=0, row=6, columnspan=4, padx=5, pady=5)

        self.checkQueue()
        self.clearErrors()

    def bid(self):
        if not self._bidding:
            return
        if self.p is not None and self.p.is_alive():
            self.after(1000, self.bid)
            return
        # Update RPM
        if self.settings['rpm'] > 0:
            self.controller.api.setRequestDelay(60/self.settings['rpm'])
        # Check if we need to update pricing
        if self.settings['autoUpdate'] and time.time() - self._lastUpdate > 3600:
            self.updatePrice()
            return
        try:
            self._bidCycle += 1
            self.p = mp.Process(target=bid, args=(
                self.q,
                self.controller.api,
                self.args['playerList'],
                self.settings
            ))
            self.p.start()
            self.controller.status.set_credits(self.controller.api.credits)
            self.after(5000, self.bid)
        except ExpiredSession:
            self.stop()
            self.controller.show_frame(Login)
        except (FutError, RequestException, ConnectionError) as e:
            self.updateLog('%s    %s: %s (%s)\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), type(e).__name__, e.reason, e.code))
            self._errorCount += 1
            if self._errorCount >= 3:
                self._banWait = self._banWait + 1
                self.updateLog('%s    Too many errors. Will resume in %d minutes...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), self._banWait*5))
                self.stop()
                login = self.controller.get_frame(Login)
                login.logout(switchFrame=False)
                self.after(self._banWait*5*60000, self.relogin, (login))
            else:
                self.after(2000, self.bid)
            pass

    def start(self, skip=False):
        if not self._bidding:
            if self.controller.api is None:
                login = self.controller.get_frame(Login)
                self.relogin(login)
            if not skip:
                self.donate()
            self._bidding = True
            self._bidCycle = 0
            self._errorCount = 0
            self._startTime = time.time()
            self.bidbtn.config(text='STOP Bidding', command=self.stop)
            self.update_idletasks()
            self.updateLog('%s    Started bidding...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
            self.bid()

    def donate(self):
        # only ask for donations once a day
        if time.time() - self._lastDonate < 86400:
            return
        # Update RPM
        if self.settings['rpm'] > 0:
            self.controller.api.setRequestDelay(60/self.settings['rpm'])
        credits = self.controller.api.credits
        login = self.controller.get_frame(Login)
        platform = login.platform.get()
        donateMsg = 'donate 10k coins to the developer' if platform == 'xbox' else 'make a small donation through PayPal'
        if credits >= 100000:
            self._lastDonate = time.time()
            self.save_settings()
            if messagebox.askyesno("Donate", "Wow, you've got %s coins! Did we help make all that money? If so, you should consider making a small donation.\n\nWould you like to %s?" % (locale.format("%d", int(credits), grouping=True), donateMsg), icon='question'):
                if platform == 'xbox':
                    self.updateLog('%s    Negotiating donation...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                    try:
                        r = requests.post('http://fifa.hunterjm.com/donate')
                        if r.status_code == 200:
                            r = r.json()
                            search = self.controller.api.searchAuctions('player', assetId=r['assetId'], min_price=r['startingBid'], max_price=r['startingBid'], min_buy=r['buyNowPrice'], max_buy=r['buyNowPrice'])
                            if self.controller.api.bid(r['tradeId'], r['buyNowPrice']):
                                self.controller.api.quickSell(r['id'])
                                self.updateLog('%s    Thank you so much for supporting this application!\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                            else:
                                self.updateLog('%s    Unfortunately, the donation did not go through.  Please try again later.\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                        else:
                            self.updateLog('%s    Unfortunately, the donation did not go through.  Please try again later.\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                    except (FutError, RequestException):
                        self.updateLog('%s    Unfortunately, the donation did not go through.  Please try again later.\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                else:
                    webbrowser.open_new_tab('https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=hunterjm%40gmail%2ecom&lc=US&item_name=FIFA%2016%20Auto%20Buyer&item_number=futgui&currency_code=USD&bn=PP%2dDonationsBF%3abtn_donateCC_LG%2egif%3aNonHosted')

    def stop(self):
        if self._bidding:
            if self.p is not None and self.p.is_alive():
                self.p.terminate()
            self._bidding = False
            self._bidCycle = 0
            self._errorCount = 0
            self.controller.status.set_status('Set Bid Options...')
            self.bidbtn.config(text='Start Bidding', command=self.start)
            self.update_idletasks()
            self.updateLog('%s    Stopped bidding...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))

    def updatePrice(self):
        self.updateLog('%s    Updating Prices for Player List...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
        self._updatedItems = []
        # it takes around 3 searches per player, based on RPM
        wait = (60/self.settings['rpm']) * 3 * len(self.args['playerList'])
        self.updateLog('%s    This is going to take around %.1f minute(s)...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), wait/60))
        self.p = mp.Process(target=lowestBin, args=(
            self.q,
            self.controller.api,
            [item['player']['id'] for item in self.args['playerList']]
        ))
        self.p.start()
        self._lastUpdate = time.time()
        self.after(int(wait*1000), self.bid)

    def setPrice(self, item, sell):
        item['buy'] = roundBid(sell*self.settings['buy'])
        item['sell'] = roundBid(sell*self.settings['sell'])
        item['bin'] = roundBid(sell*self.settings['bin'])
        self.tree.set(item['player']['id'], 'buy', item['buy'])
        self.tree.set(item['player']['id'], 'sell', item['sell'])
        self.tree.set(item['player']['id'], 'bin', item['bin'])
        playersearch = self.controller.get_frame(PlayerSearch)
        playersearch.tree.set(item['player']['id'], 'buy', item['buy'])
        playersearch.tree.set(item['player']['id'], 'sell', item['sell'])
        playersearch.tree.set(item['player']['id'], 'bin', item['bin'])
        self.save_list()
        displayName = item['player']['commonName'] if item['player']['commonName'] is not '' else item['player']['lastName']
        self.updateLog('%s    Setting %s to %d/%d/%d (based on %d)...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), displayName, item['buy'], item['sell'], item['bin'], sell))
        return item

    def lookup_bin(self, player):
        # lookup BIN
        r = {'xbox': 0, 'ps4': 0}
        displayName = player['commonName'] if player['commonName'] is not '' else player['lastName']
        response = requests.get('http://www.futbin.com/pages/16/players/filter_processing.php', params={
            'start': 0,
            'length': 30,
            'search[value]': displayName
        }).json()
        for p in response['data']:
            if p[len(p)-2] == player['id']:
                if not p[6]: p[6] = 0
                if not p[8]: p[8] = 0
                r = {'xbox': int(p[8]), 'ps4': int(p[6])}
        return r

    def checkQueue(self):
        try:
            msg = self.q.get(False)
            if isinstance(msg, FutError):
                # Exception
                self.updateLog('%s    %s: %s (%s)\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), type(msg).__name__, msg.reason, msg.code))
                if isinstance(msg, ExpiredSession):
                    self._errorCount += 3
                else:
                    self._errorCount += 1
                if self._errorCount >= 3:
                    self._banWait = self._banWait + 1
                    self.updateLog('%s    Too many errors. Will resume in %d minutes...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), self._banWait*5))
                    self.stop()
                    login = self.controller.get_frame(Login)
                    login.logout(switchFrame=False)
                    self.after(self._banWait*5*60000, self.relogin, (login))
            elif isinstance(msg, DelayedCore):
                self.controller.api = msg
            elif isinstance(msg, tuple):
                if isinstance(msg[0], Card) and isinstance(msg[1], EventType):
                    if msg[1] == EventType.BIDWAR:
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid, tag='war')
                    elif msg[1] == EventType.NEWBID:
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid, tag='bid')
                    elif (msg[1] == EventType.LOST or msg[1] == EventType.OUTBID):
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid, tag='lost')
                    elif (msg[1] == EventType.BIDWON or msg[1] == EventType.BIN):
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid, tag='won')
                    elif msg[1] == EventType.SELLING:
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid, tag='selling')
                    elif msg[1] == EventType.SOLD:
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid, tag='sold')
                    elif msg[1] == EventType.UPDATE:
                        self.auctionStatus.update_status(msg[0], time.strftime('%Y-%m-%d %H:%M:%S'), msg[0].currentBid)
                    self.controller.status.set_credits(msg[2])
                else:
                    # Auction Results
                    self.auctionsWon += msg[0]
                    self.sold += msg[1]
                    self.controller.status.set_credits(msg[2])
                    self.controller.status.set_stats((self.auctionsWon, self.sold))
                    self.controller.status.set_status('Bidding Cycle: %d' % (self._bidCycle))
                    if time.time() - self._startTime > 18000:
                        self.updateLog('%s    Pausing to prevent ban... Will resume in 1 hour...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                        self.stop()
                        login = self.controller.get_frame(Login)
                        login.logout(switchFrame=False)
                        self.after(60*60000, self.relogin, (login))
            elif isinstance(msg, dict):
                # Update Pricing
                self._lastUpdate = time.time()
                for item in self.args['playerList']:
                    # Skip those that are finished
                    if item['player']['id'] in self._updatedItems:
                        continue
                    if item['player']['id'] == msg['defId']:
                        displayName = item['player']['commonName'] if item['player']['commonName'] is not '' else item['player']['lastName']
                        if msg['num'] > 10:
                            bid = msg['lowestBIN'] - increment(msg['lowestBIN'])
                            self.updateLog('%s    %d %s listed... Lowering Bid to %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg['num'], displayName, bid))
                        else:
                            bid = msg['lowestBIN']
                            self.updateLog('%s    %d %s listed... Setting Bid to %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), msg['num'], displayName, bid))
                        item = self.setPrice(item, bid)
                        break
            else:
                # Normal Message
                self._banWait = 0
                self.updateLog(msg)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.checkQueue)

    def relogin(self, login):
        login.login(switchFrame=False)
        self.start(True)

    def clearErrors(self):
        if self._bidding and self._errorCount > 0:
            self._errorCount = self._errorCount - 1
        self.after(900000, self.clearErrors)

    def updateLog(self, msg):
        self.logView.insert('end', msg)
        self.logView.see(tk.END)
        self.update_idletasks()

    def save_list(self):
        self.args['playerFile'][self.controller.user] = self.args['playerList']
        with open(constants.PLAYERS_FILE, 'w') as f:
                json.dump(self.args['playerFile'], f)

    def save_settings(self, *args):
        try:
            self.settings = {
                'rpm': int(self.rpm.get()) if self.rpm.get() else 0,
                'minCredits': int(self.minCredits.get()) if self.minCredits.get() else 0,
                'maxPlayer': int(self.maxPlayer.get()) if self.maxPlayer.get() else 0,
                'autoUpdate': self.autoUpdate.get(),
                'buy': int(self.buy.get())/100 if self.buy.get() else 0,
                'sell': int(self.sell.get())/100 if self.sell.get() else 0,
                'bin': int(self.bin.get())/100 if self.bin.get() else 0,
                'snipeOnly': self.snipeOnly.get(),
                'relistAll': self.relistAll.get(),
                'donate': self._lastDonate
            }
            with open(constants.SETTINGS_FILE, 'w') as f:
                    json.dump(self.settings, f)
        except:
            pass

    def playersearch(self):
        self.stop()
        self.controller.show_frame(PlayerSearch)

    def active(self):
        if self.controller.api is None:
            self.controller.show_frame(Login)

        Base.active(self)
        self.logView.delete(1.0, tk.END)
        self.updateLog('%s    Set Bid Options...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
        self.controller.status.set_status('Set Bid Options...')
        self.tree.delete(*self.tree.get_children())
        for item in self.args['playerList']:
            displayName = item['player']['commonName'] if item['player']['commonName'] is not '' else item['player']['lastName']
            try:
                self.tree.insert('', 'end', item['player']['id'], text=displayName, values=(item['buy'], item['sell'], item['bin']))
            except:
                pass

        self._lastUpdate = 0
        self._updatedItems = []
        self.auctionsWon = 0
        self.sold = 0

from frames.login import Login
from frames.playersearch import PlayerSearch
from fut.exceptions import FutError, ExpiredSession
from requests.exceptions import RequestException, ConnectionError
