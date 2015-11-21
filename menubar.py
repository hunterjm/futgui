import tkinter as tk


class MenuBar(tk.Menu):
    def __init__(self, parent):
        tk.Menu.__init__(self, parent)

        # appmenu = tk.Menu(self, name='apple')
        # self.add_cascade(menu=appmenu)
        # appmenu.add_command(label='About My Application')
        # appmenu.add_separator()

        # filemenu = tk.Menu(self, tearoff=False)
        # self.add_cascade(label="File",underline=0, menu=filemenu)
        # filemenu.add_command(label="Load Buyer Plan", command=self.callback)
        # filemenu.add_command(label="Save Buyer Plan", command=self.callback)
        # filemenu.add_separator()
        # filemenu.add_command(label="Exit", underline=1, command=self.quit)

        # helpmenu = tk.Menu(self, tearoff=False)
        # self.add_cascade(label="Help", menu=helpmenu)
        # helpmenu.add_command(label="About...", command=self.callback)
