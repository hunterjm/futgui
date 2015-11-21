import tkinter as tk
import sys
import core.constants as constants
import os.path

from tkinter import messagebox
from PIL import ImageTk, Image
from frames.loading import Loading
from frames.playersearch import PlayerSearch
from frames.login import Login
from frames.bid import Bid
from frames.watch import Watch


class Application(tk.Frame):
    def __init__(self, master):
        if not self.prepare_environment():
            messagebox.showerror("Error", "Unable to write to your home directory.\n"
                                          "Make sure {0} exists and it is writable".format(constants.SETTINGS_DIR))
            sys.exit(1)

        self.api = None
        self.user = None
        self.status = master.status
        tk.Frame.__init__(self, master, bg='#1d93ab')

        # the container is where we'll stack a bunch of frames
        # on top of each other, then the one we want visible
        # will be raised above the others
        container = tk.Frame(self, bg='#1d93ab')
        container.pack(side="top", fill="both", expand=True, padx=15, pady=15)
        container.grid_rowconfigure(0, weight=0)
        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(0, weight=1)

        fifaImg = ImageTk.PhotoImage(Image.open('images/logo_icon.jpg'))
        fifaLabel = tk.Label(container, bg='#1d93ab', image=fifaImg)
        fifaLabel.grid(column=0, row=0, sticky='w')
        fifaLabel.image = fifaImg

        self.frames = {}
        for F in (Loading, Login, PlayerSearch, Bid, Watch):
            frame = F(container, self)
            self.frames[F] = frame
            # put all of the pages in the same location;
            # the one on the top of the stacking order
            # will be the one that is visible.
            frame.grid(column=0, row=1, sticky='news')

        self.show_frame(Login)

    def show_frame(self, c, **kwargs):
        '''Show a frame for the given class'''
        frame = self.frames[c]
        frame.set_args(kwargs)
        frame.tkraise()
        frame.active()

    def get_frame(self, c):
        return self.frames[c]

    def prepare_environment(self):
        """
        Prepare the environment, namely ensures that the settings folder exists and it is writeable
        :return: true if the environment is sane, false otherwise
        """
        if not os.path.exists(constants.SETTINGS_DIR):
            os.makedirs(constants.SETTINGS_DIR)

        return os.access(constants.SETTINGS_DIR, os.W_OK)
