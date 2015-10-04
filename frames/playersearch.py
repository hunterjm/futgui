import tkinter as tk
from frames.base import Base
import json, requests
import time
import multiprocessing as mp
from PIL import Image, ImageTk
from core.playercard import create

class PlayerSearch(Base):
    def __init__(self, master, controller):
        Base.__init__(self, master, controller)
        self.master = master
        self.url = 'https://www.easports.com/uk/fifa/ultimate-team/api/fut/item'
        self._job = None
        self.player = tk.StringVar()
        self._playerName = ''
        search = tk.Entry(self, textvariable=self.player)
        search.bind('<KeyRelease>', self.search)
        search.bind('<Return>', self.lookup)
        search.grid(column=0, row=0, sticky='we')

        #preload cards and info
        self.cards = {
            'group0': Image.open('images/cards/group0.png'),
            'group1': Image.open('images/cards/group1.png'),
            'group2': Image.open('images/cards/group2.png')
        }
        with open('images/cards/cards_big.json', 'r') as f:
                self.cardinfo = json.load(f)

        self.cardLabels = None

        #create scrolling frame
        # create a canvas object and a vertical scrollbar for scrolling it
        hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(column=0, row=2, sticky='we')
        canvas = tk.Canvas(self, bd=0, highlightthickness=0, bg='#1d93ab', xscrollcommand=hscrollbar.set)
        canvas.grid(column=0, row=1, sticky='news')
        hscrollbar.config(command=canvas.xview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(canvas, bg='#1d93ab')
        interior_id = canvas.create_window(0, 0, window=interior,
                                           anchor=tk.NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqheight() != canvas.winfo_height():
                # update the canvas's width to fit the inner frame
                canvas.config(height=interior.winfo_reqheight())
        interior.bind('<Configure>', _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqheight() != canvas.winfo_height():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, height=canvas.winfo_height())
        canvas.bind('<Configure>', _configure_canvas)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

    def search(self, event=None):
        self.kill_job()

        # make sure it's a different name
        if self._playerName != self.player.get():
            self._playerName = self.player.get()
            self._job = self.after(500, self.lookup)

    def lookup(self, event=None):
        self.kill_job()
        payload = {'jsonParamObject': json.dumps({'name': self._playerName})}
        response = requests.get(self.url, params=payload).json()
        count = response['count']# if response['count'] < 5 else 5
        self.controller.status.set_status('Found %d matches for "%s"' % (response['totalResults'], self._playerName))
        for child in self.interior.winfo_children():
            child.destroy()
        p = mp.Pool(processes=mp.cpu_count())
        # results = p.apply_async(PlayerCard, (self, response['items']))
        results = [p.apply_async(create, (player,)) for player in response['items']]
        self.master.config(cursor='wait')
        self.master.update()
        i = 0;
        for r in results:
            self.load_player(r.get(), response['items'][i])
            i += 1
        self.master.config(cursor='')
        self.master.update()

    def load_player(self, result, player):
        # make card
        img = ImageTk.PhotoImage(result)
        lbl = tk.Label(self.interior, bg='#1d93ab', image=img)
        lbl.pack(side='left')
        lbl.config(cursor='pencil')
        lbl.image = img
        self.update_idletasks()
        lbl.bind("<Button-1>", lambda e, player=player: self.show_bid(player))

    def show_bid(self, player):
        displayName = player['commonName'] if player['commonName'] is not '' else player['lastName']
        self.controller.status.set_status('Setting bid options for %s...' % displayName)
        self.controller.show_frame(Bid, player=player)

    def kill_job(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def active(self):
        Base.active(self)
        if self.controller.api is None:
            self.controller.show_frame(Login)


from frames.login import Login
from frames.bid import Bid