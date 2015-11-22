import tkinter as tk


class Base(tk.Frame):
    def __init__(self, master, controller):
        self.controller = controller
        self.args = {}
        # init frame
        tk.Frame.__init__(self, master, bg='#1d93ab')

    def set_args(self, argDict):
        self.args = argDict

    def active(self):
        self.update()
