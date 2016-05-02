#!/usr/bin/env python3
import re
import random

from tkinter import *
from tkinter.ttk import *

# Import Tk standard dialogs
from tkinter import filedialog
import mailmanager_stub as mms
from prefsform import PrefsForm
from composeform import ComposeForm
from mailmanager import *
from threading import Thread
import getpass
from tkinter import messagebox

WORD_REGEX = re.compile(r"\*([a-z]+)\*")

class WordTable(Frame):
    """Create a table view of words, their parts of speech, and use count."""
    def __init__(self, parent, text_table):
        super().__init__(parent)
        self._items = []    # Hack to keep track of currently-inserted words
        self.dicOfMsg = {}
        self.position = 0
        
        # Build a tree view and populate it with the words
        # (We don't use this as a tree per se, just as a multi-column list)
        # (notice that the first column is implicit; we list only the 2nd and 3rd
        # columns here; also, we don't want the user to be able to select anything)
        self._tv = Treeview(self, columns=["from", "part", "count", "position"], selectmode="none")
        
        # Set column properties
        self._tv.column("#0", width=60, stretch=False) # Column #0 means the "primary" (leftmost) column
        self._tv.column("from", width=300, stretch=True)
        self._tv.column("part", width=350, stretch=True)
        self._tv.column("count", width=200, stretch=True)
        self._tv.column("position", width=0, stretch=False)
        # Set column captions
        self._tv.heading("#0", text="Delete")
        self._tv.heading("from", text="From")
        self._tv.heading("part", text="Subject")
        self._tv.heading("count", text="Date")
        self._tv.heading("position", text="")
        
        # Make a scrollbar for us, too
        scrolly = Scrollbar(self, orient=VERTICAL, command=self._tv.yview)
        self._tv["yscrollcommand"] = scrolly.set
        
        self._tv.bind("<Double-1>", lambda event, table=text_table: self._click_tag(event, table))            #  //This is what I will have to implement


        # Pack 'em in...
        scrolly.pack(side=RIGHT, fill=Y)
        self._tv.pack(expand=YES, fill=BOTH)

    #difining my own methods
    def load_msg(self, message):
        sender = message.sender
        subject = message.subject
        date = message.date
        smg = message.text

        if not (date.replace(" ", "") + subject.replace(" ", "")) in self.dicOfMsg:
            self._items.append(date.replace(" ", "") + subject.replace(" ", ""))
            self.dicOfMsg[date.replace(" ", "") + subject.replace(" ", "")] = message

            self._tv.insert('',     # No parent (top-level item in "tree")
            END,                # Insert at END of list
            date.replace(" ", "") + subject.replace(" ", ""),               # Use the word itself as the item ID
            text="NO",          # Display the word itself in column #0
            values=(sender, subject, date, self.position)) # Put the part of speech and count in the other columns
            self.position += 1


    def _click_tag(self, event, table):
        # Figure out exactly which tag-span was clicked                 lambda event, arg=data: self.on_mouse_down(event, arg)
        part = self._tv.identify('item',event.x,event.y)
        self._tv.selection_set(part)
        wmap = self.dicOfMsg[part]
        table.load_msg(wmap)

        capi = self._tv.item(part, "text")
        if capi == "NO":
            self._tv.item(part, text="YES")
        else:
            self._tv.item(part, text="NO")
        
        
        #table.delete_msg()

    def delete_selected_msg(self, table):
        deltedPosition = []
        check = False
        x = self._tv.get_children()
        table.delete_msg()
        for item in x: ## Changing all children from root item
            eliminar = self._tv.item(item, "text")
            if eliminar == "YES":
                position = self._tv.item(item, "values")
                self._tv.delete(item)
                del self.dicOfMsg[item]
                num = position[3]
                deltedPosition.append(num)
                check = True

        #print(self.dicOfMsg)
        return check, deltedPosition


    def getItemFocus(self):
        toReply = ""
        item = self._tv.focus()
        try:
            eliminar = self._tv.item(item, "values")
            toReply = eliminar[3]
        except Exception as e:
            print("")
        return toReply




class MadlibText(Frame):
    """A compound widget for playing MadLib.
    
    Must have a WordMap object and a text "story" to work;
    both of these are provided after object creation via
    the "load_wordmap" and "load_story" methods.
    """
    def __init__(self, parent):
        super().__init__(parent)
        
        # No wordmap yet
        self._wordmap = None
        self._msg = None
        
        # Wire up text/scrollbar widgets
        self._text = Text(self, wrap="word")
        #text.config(state=DISABLED)
        scrolly = Scrollbar(self, orient=VERTICAL, command=self._text.yview)
        self._text['yscrollcommand'] = scrolly.set
        
        # Pack them into the containing frame
        scrolly.pack(side=RIGHT, fill=Y)
        self._text.pack(expand=YES, fill=BOTH)


    
    def load_msg(self, message):
        # Clear out all text
        self._text.delete("1.0", END)

        self._msg = "From: %s \nTo: %s \nDate: %s \nSubject: %s \n\n\n\n%s" % (message.sender, "Capivara", message.date, message.subject, message.text)
        
        # Update the text view
        self._text.insert(END, self._msg)

    def delete_msg(self):
        # Clear out all text
        self._text.delete("1.0", END)



class MadlibApp:
    def __init__(self):
        root = Tk()
        self._root = root
        root.title("tkMadLib")
        self._style = Style(self._root)
        self._style.theme_use("clam")


        self.mailManager = MailManager(getpass.getuser(), "",  "csunix.cs.bju.edu")
        self.msgList = []
        self.getMailThread = None
        self.deleteThread = None
        
        # Resizable panes, side-by-side
        panes = PanedWindow(root, orient=VERTICAL)
        
        # Left side: a word table and a set of buttons
        frame = Frame(panes)
        
        panel = Frame(frame)
        btn_newMsg = Button(panel, text="New Message", command=self._newMsg)
        btn_newMsg.pack(side=LEFT, padx=5, pady=5)
        btn_reply = Button(panel, text="Reply", command=self._reply)
        btn_reply.pack(side=LEFT, padx=5, pady=5)
        btn_delete = Button(panel, text="Delete", command=self._deleteMsg)
        btn_delete.pack(side=LEFT, padx=5, pady=5)
        btn_getMail = Button(panel, text="Get Mail", command=self._getMail)
        btn_getMail.pack(side=LEFT, padx=5, pady=5)
        btn_config = Button(panel, text="Configure", command=self._config)
        btn_config.pack(side=LEFT, padx=5, pady=5)
        panel.pack(side=TOP, fill=X)


        #Right side: the scrolling text view
        self._text = MadlibText(panes)

        self._table = WordTable(frame, self._text)
        self._table.pack(expand=YES, fill=BOTH)
        

        # Complete the layout
        panes.add(frame)
        panes.add(self._text)    
        panes.pack(expand=YES, fill=BOTH)

        ##My command definitions
    
    def _config(self):
        self.prefsForm = PrefsForm(self, self.mailManager)


    def _getMail(self):
    	#self.obtainedMsgs = mms.MailManager_Stub.getMail()
        #for i in self.obtainedMsgs:
            #wordmap = WordMap(i)
            #self._table.load_msg(wordmap)
        self.result = []

        connectResult = self.mailManager.connect()
        if connectResult == self.mailManager.CONNECT_LOGIN_SUCCESS or connectResult == self.mailManager.ALREADY_CONNECTED:
            nMsgs = self.mailManager.getNumMessages()
            self.maxProgress = nMsgs
            for i in range(nMsgs): #range(nMsgs)
                msg = self.mailManager.getMessage(i)
                self.result.append(msg)
                self.msgList.append(msg)
            self.mailManager.disconnect()
        else:
            messagebox.showinfo("Oops", "Unable to get emails.")
            return


        for msg in self.result:
            print(msg.sender)
            print(msg.subject)
            print(msg.date)
            print(msg.text)
            print("\n")
            self._table.load_msg(msg)


    def _deleteMsg(self):

        deleted, positions = self._table.delete_selected_msg(self._text)

        if len(positions) == 0:
            messagebox.showinfo("", "There are no messages to delete.")
            return

        if not deleted:
            messagebox.showinfo("Oops", "Select a message to delete.")
            return

        connectResult = self.mailManager.connect()
        for i in positions:
            if self.mailManager.deleteMessage(int(i)):
                del self.msgList[int(i)]
                print("deleted something for now")
        self.mailManager.disconnect()


    def _newMsg(self):
        self.composeForm = ComposeForm(self, self.mailManager.userid)


    def _reply(self):
        msgIndex = self._table.getItemFocus()
        if msgIndex != "":
            msg = self.msgList[int(msgIndex)]
            self.composeForm = ComposeForm(self, self.mailManager.userid, msg.sender)
        else:
            messagebox.showinfo("Oops", "You must select a message before you can reply to it.")


    
    def run(self):
        """Run the application to termination."""
        self._root.mainloop()





if __name__ == "__main__":
    MadlibApp().run()
