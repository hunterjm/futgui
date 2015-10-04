import tkinter as tk
from frames.base import Base
from PIL import Image, ImageTk

class Loading(Base):
    def __init__(self, master, controller):
        Base.__init__(self, master, controller)
        loading = ImageTk.PhotoImage(Image.open('images/loading.jpg'))
        label = tk.Label(self, bg='#1d93ab', image=loading)
        label.image = loading
        label.pack(expand=True)