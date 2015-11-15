import tkinter.ttk as ttk

class AuctionStatus():

    def __init__(self, frame):
        t = ttk.Treeview(frame)
        t['columns'] = ('timestamp', 'initial bid', 'current bid', 'bin')
        t.column("timestamp",width=75)
        t.column("initial bid", width=50)
        t.column("current bid", width=50)
        t.column("bin", width=50)
        t.heading("#0", text="Card name", anchor="w")
        t.heading("initial bid", text="initial bid")
        t.heading("current bid", text="current bid")
        t.heading("bin", text="BIN")

        t.heading("timestamp",text="timestamp")
        t.heading("initial bid", text="initial bid")
        t.heading("current bid", text="current bid")
        t.heading("bin", text="BIN")

        t.insert("",0,"dir1",text="directory 1")
        t.insert("dir1","end","dir 1",text="file 1 1",values=("file 1 A","file 1 B"))
        t.insert("", "end", "Alonso", text="Alsd", values=("foo", "bar"))

        self.view = t

    def get_view(self):
        return self.view

    def add_status(self, cardid, cardname, timestamp, initbid, currbid, bin):
        return self.view.insert("", 'end', cardid, text=cardname, values=(timestamp, initbid, currbid, bin))

    def change_status(self, item, values):
        index = self.view.index(item)
        itemtext = self.view.item(item)['text']

        self.view.delete(item)
        return self.view.insert("", index, item, text=itemtext, values=values)
