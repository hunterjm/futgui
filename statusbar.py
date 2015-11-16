import tkinter as tk
import locale

from PIL import ImageTk, Image

locale.setlocale(locale.LC_ALL, '')

class StatusBar(tk.Frame):

    def __init__(self, master):
        tk.Frame.__init__(self, master, bg='#31718f')
        self.label = tk.Label(self, fg='#fcca00', bg='#31718f', font=('KnulBold', 12, 'bold'))
        self.label.grid(column=0, row=0, sticky='w')
        self.stats = tk.Label(self, fg='#fcca00', bg='#31718f', font=('KnulBold', 12))
        self.stats.grid(column=1, row=0, sticky='w')
        coinImg = ImageTk.PhotoImage(Image.open('images/coins.jpg'))
        coinLabel = tk.Label(self, bg='#31718f', image=coinImg)
        coinLabel.grid(column=2, row=0, sticky='e')
        coinLabel.image = coinImg
        self.credits = tk.Label(self, fg='#fcca00', bg='#31718f', font=('KnulBold', 12))
        self.credits.grid(column=3, row=0, sticky='w')
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_columnconfigure(2, weight=0)
        self.grid_columnconfigure(3, weight=0)
        self.grid_rowconfigure(0, weight=1)

    def set_status(self, format, *args):
        self.label.config(text=format % args)
        self.label.update_idletasks()

    def clear_status(self):
        self.label.config(text="")
        self.label.update_idletasks()

    def set_stats(self, stats):
        self.stats.config(text='Won: %d - Sold: %d' % stats)
        self.stats.update_idletasks()

    def set_credits(self, credits):
        credits = locale.format("%d", int(credits), grouping=True)
        self.credits.config(text=credits)
        self.credits.update_idletasks()