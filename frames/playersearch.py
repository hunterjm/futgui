import tkinter as tk
import json
import requests
import multiprocessing as mp
import core.constants as constants

from core.editabletreeview import EditableTreeview
from os.path import expanduser
from frames.base import Base
from PIL import Image, ImageTk
from core.playercard import create
from core.model.player import Player, PlayerEncoder


class PlayerSearch(Base):
    def __init__(self, master, controller):
        Base.__init__(self, master, controller)
        self.master = master
        self.url = 'https://www.easports.com/uk/fifa/ultimate-team/api/fut/item'

        # Track the current job to be able to interrupt it, if needed
        self._job = None

        # Track the currently searched player name
        self.searchedPlayerName = ''

        # Add search bar
        self.issuedPlayerName = tk.StringVar()
        search = tk.Entry(self, textvariable=self.issuedPlayerName)
        search.bind('<KeyRelease>', self.search)
        search.bind('<Return>', self.lookup)
        search.grid(column=0, row=0, columnspan=2, sticky='we')

        # preload cards and info
        self.cards = {
            'group0': Image.open('images/cards/group0.png'),
            'group1': Image.open('images/cards/group1.png'),
            'group2': Image.open('images/cards/group2.png')
        }
        with open('images/cards/cards_big.json', 'r') as f:
                self.cardinfo = json.load(f)

        self.cardLabels = None

        # create scrolling frame
        # create a canvas object and a vertical scrollbar for scrolling it
        hscrollbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(column=0, row=2, columnspan=2, sticky='we')
        canvas = tk.Canvas(self, bd=0, highlightthickness=0, bg='#1d93ab', xscrollcommand=hscrollbar.set)
        canvas.grid(column=0, row=1, columnspan=2, sticky='news')
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

        # Add a treeview to display selected players
        self.tree = EditableTreeview(self, columns=('position', 'rating', 'buy', 'sell', 'bin', 'enabled', 'actions'), selectmode='browse', height=8)
        self.tree.heading('#0', text='Name', anchor='w')
        self.tree.column('position', width=100, anchor='center')
        self.tree.heading('position', text='Position')
        self.tree.column('rating', width=100, anchor='center')
        self.tree.heading('rating', text='Rating')
        self.tree.column('buy', width=100, anchor='center')
        self.tree.heading('buy', text='Purchase For')
        self.tree.column('sell', width=100, anchor='center')
        self.tree.heading('sell', text='Sell For')
        self.tree.column('bin', width=100, anchor='center')
        self.tree.heading('bin', text='Sell For BIN')
        self.tree.column('enabled', width=50, anchor='center')
        self.tree.heading('enabled', text='Enabled')
        self.tree.column('actions', width=20, anchor='center')
        self.tree.bind('<<TreeviewInplaceEdit>>', self._on_inplace_edit)
        self.tree.bind('<<TreeviewCellEdited>>', self._on_cell_edited)
        self.tree.grid(column=0, row=3, columnspan=2, sticky='we')

        watchbtn = tk.Button(self, text='Watch Player', command=self.show_watch)
        watchbtn.grid(column=0, row=4, sticky='we')

        bidbtn = tk.Button(self, text='Start Bidding', command=self.show_bid)
        bidbtn.grid(column=1, row=4, sticky='we')

        self._del_btn = tk.Button(self.tree, text='-', command=self._on_del_clicked)

        # Load existing players
        self.load_players_from_file()

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)

    def load_players_from_file(self):
        try:
            with open(constants.PLAYERS_FILE, 'r') as f:
                self.allPlayers = json.load(f)
        except Exception as e:
            print("Error while loading players file")
            self.allPlayers = {}

        # At this stage, allPlayers is a dictionary of lists of dictionaries
        for user in self.allPlayers:
            userPlayersList = self.allPlayers[user]
            userPlayers = [Player(p) for p in userPlayersList]
            self.allPlayers[user] = userPlayers

    def search(self, event=None):
        self.kill_job()

        # make sure it's a different name
        if self.searchedPlayerName != self.issuedPlayerName.get():
            self.searchedPlayerName = self.issuedPlayerName.get()
            self._job = self.after(500, self.lookup)

    def lookup(self, event=None):
        self.kill_job()
        payload = {'jsonParamObject': json.dumps({'name': self.searchedPlayerName})}
        response = requests.get(self.url, params=payload).json()
        self.controller.status.set_status('Found %d matches for "%s"' % (response['totalResults'], self.searchedPlayerName))
        for child in self.interior.winfo_children():
            child.destroy()
        p = mp.Pool(processes=mp.cpu_count())
        results = [p.apply_async(create, (player,)) for player in response['items']]
        self.master.config(cursor='wait')
        self.master.update()

        # Load a player card for each result
        i = 0
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

        # Bind an action that will add a player in the list on click
        lbl.bind("<Button-1>", lambda e, player=player: self.add_player(Player(
            { 'player': player, 'buy': 0, 'sell': 0, 'bin': 0
              })
        ))

    def add_player(self, player, write=True):
        try:
            self.tree.insert('', 'end', player.playerid, text=player.displayName, values=(player.position,
                                player.rating, player.maxBuy, player.sell, player.bin, player.enabled))
        except:
            pass

        if write:
            self.userPlayers.append(player)
            self.save_players_list()

    def save_players_list(self):
        self.allPlayers[self.controller.user] = self.userPlayers
        with open(constants.PLAYERS_FILE, 'w') as f:
            json.dump(self.allPlayers, f, cls=PlayerEncoder)

    def _on_inplace_edit(self, event):
        col, item = self.tree.get_event_info()
        if col in ('buy', 'sell', 'bin'):
            self.tree.inplace_entry(col, item)
        elif col in ('actions',):
            self.tree.inplace_custom(col, item, self._del_btn)
        elif col in ('enabled',):
            self.tree.inplace_checkbutton(col, item, onvalue="yes", offvalue="no")

    def _on_del_clicked(self):
        sel = self.tree.selection()
        if sel:
            p_id = sel[0]
            self.tree.delete(p_id)
            del self.userPlayers[next(i for (i, player) in enumerate(self.userPlayers) if player.playerid == p_id)]
            self.save_players_list()

    def _on_cell_edited(self, event):
        col, item = self.tree.get_event_info()
        values = self.tree.item(item, 'values')
        for player in self.userPlayers:
            if player.playerid == item:
                player.maxBuy = int(values[2])
                player.sell = int(values[3])
                player.bin = int(values[4])
                player.enabled = str(values[5])
                break
        self.save_players_list()

    def show_bid(self):
        if len(self.userPlayers) > 0:
            # pass the list of only enabled players
            enabledPlayers = list(filter(lambda x: x.enabled == 'yes', self.userPlayers))
            self.controller.show_frame(Bid, userPlayers=enabledPlayers)

    def show_watch(self):
        sel = self.tree.selection()
        if sel:
            p_id = sel[0]
            player = next(filter(lambda x: x.playerid == p_id, self.userPlayers))
            self.controller.show_frame(Watch, player=player.details)
        else:
            from tkinter import messagebox
            messagebox.showerror("Error","Select a player from the list first!")

    def kill_job(self):
        if self._job is not None:
            self.after_cancel(self._job)
            self._job = None

    def active(self):
        Base.active(self)
        if self.controller.api is None:
            self.controller.show_frame(Login)

        # Check if we have a list for this user
        if self.controller.user not in self.allPlayers:
            self.allPlayers[self.controller.user] = []

        # Extract from the all players file only the players belonging to the current user
        self.userPlayers = self.allPlayers[self.controller.user]

        # Add each player to the list
        for player in self.userPlayers:
            self.add_player(player, write=False)

from frames.login import Login
from frames.watch import Watch
from frames.bid import Bid
