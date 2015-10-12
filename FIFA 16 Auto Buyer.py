#!/usr/bin/env python3

import tkinter as tk
import multiprocessing as mp
from menubar import MenuBar
from statusbar import StatusBar
from application import Application

class MainApplication(tk.Tk):
    """Container for all frames within the application"""

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        #initialize menu
        self.config(menu=MenuBar(self))
        self.title('FIFA 16 Auto Buyer')
        self.geometry('850x600-5+40')
        self.minsize(width=650, height=450)

        # bind ctrl+a
        self.bind_class("Entry", "<Control-a>", self.selectall)
        self.bind_class("Entry", "<Command-a>", self.selectall)

        self.status = StatusBar(self)
        self.status.pack(side='bottom', fill='x')
        self.status.set_credits('0')

        self.appFrame = Application(self)
        self.appFrame.pack(side='top', fill='both', expand='True')

    def selectall(self, e):
        e.widget.select_range(0, tk.END)


if __name__ == '__main__':
    mp.freeze_support()
    app = MainApplication()
    app.lift()
    app.mainloop()