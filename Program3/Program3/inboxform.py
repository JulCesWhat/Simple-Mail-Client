#!/usr/bin/env python3

# Filename: inboxform.py
# Project: CpS 320 Program 3 - PyMail
# Author: Julio Cesar Whatley
# Date Last Modified: April 30 2016
# Description: Implements the event handlers and threads of the Inboxform.
#   The InboxForm allows the user to read and manipulate his mailbox.

from tkinter import *
from tkinter.ttk import *

from tkinter import ttk

# Import Tk standard dialogs
from tkinter import filedialog
import mailmanager_stub as mms
from prefsform import PrefsForm
from composeform import ComposeForm
from mailmanager import *
from threading import Thread
import getpass
from tkinter import messagebox

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
        self._tv = Treeview(self, columns=["part", "count", "position"], selectmode="none")
        
        # Set column properties
        self._tv.column("#0", width=300, stretch=True) # Column #0 means the "primary" (leftmost) column
        self._tv.column("part", width=350, stretch=True)
        self._tv.column("count", width=200, stretch=True)
        self._tv.column("position", width=0, stretch=False)
        # Set column captions
        self._tv.heading("#0", text="From")
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
            text=sender,          # Display the word itself in column #0
            values=(subject, date, self.position)) # Put the part of speech and count in the other columns
            self.position += 1


    def _click_tag(self, event, table):
        # Figure out exactly which tag-span was clicked                 lambda event, arg=data: self.on_mouse_down(event, arg)
        part = self._tv.identify('item',event.x,event.y)
        self._tv.selection_set(part)
        wmap = self.dicOfMsg[part]
        table.load_msg(wmap)
    

    def delete_selected_msg(self):
        item = self._tv.focus()
        if item:
            self._tv.delete(item)
            del self.dicOfMsg[item]


    def getItemFocus(self):
        toReply = ""
        item = self._tv.focus()
        try:
            eliminar = self._tv.item(item, "values")
            toReply = eliminar[2]
        except Exception as e:
            print("")
        return toReply

    def positionFocus(self):
        item = self._tv.focus()
        pos = self._tv.index(item)
        return pos




class MadlibText(Frame):
    """A compound widget for playing MadLib.
    
    Must have a WordMap object and a text "story" to work;
    both of these are provided after object creation via
    the "load_wordmap" and "load_story" methods.
    """
    def __init__(self, parent):
        super().__init__(parent)
        
        # No wordmap yet
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
        super().__init__()
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
        self.btn_newMsg = Button(panel, text="New Message", command=self._newMsg)
        self.btn_newMsg.pack(side=LEFT, padx=5, pady=5)
        self.btn_reply = Button(panel, text="Reply", command=self._reply)
        self.btn_reply.pack(side=LEFT, padx=5, pady=5)
        self.btn_delete = Button(panel, text="Delete", command=self._deleteMsg)
        self.btn_delete.pack(side=LEFT, padx=5, pady=5)
        self.btn_getMail = Button(panel, text="Get Mail", command=self._getMail)
        self.btn_getMail.pack(side=LEFT, padx=5, pady=5)
        self.btn_config = Button(panel, text="Configure", command=self._config)
        self.btn_config.pack(side=LEFT, padx=5, pady=5)
        self.btn_stop = Button(panel, text="Stop", command=self._stop)
        self.btn_stop.pack(side=RIGHT, padx=5, pady=5)
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

        # disable relevant widgets
        self.btn_delete.state(["disabled"])
        self.btn_getMail.state(["disabled"])
        self.btn_stop.state(["!disabled"])

        #spawn thread
        self.getMailThread = GetMailThread(self.mailManager)
        self.getMailThread.start()
        
        # I think that I would init init progress bar

        # Track the current timer interval with a Tk "variable"
        self._intervalGetEmail = IntVar(value=100)

        # Configure a timeout event (capture the ID for cancellation)
        self._afteridGetEmail = self._root.after(self._intervalGetEmail.get(), self.checkGetMailThread)


    def _deleteMsg(self):

        if len(self.msgList) == 0:
            messagebox.showinfo("No messages", "There are no messages to delete.")
            return

        msgIndex = self._table.positionFocus()
        print(msgIndex)

        if msgIndex == "":
            messagebox.showinfo("Oops", "Select a message to delete.")
            return

        # disable relevant widgets
        self.btn_delete.state(["disabled"])
        self.btn_getMail.state(["disabled"])
        self.btn_stop.state(["!disabled"])

        # spawn thread
        self.deleteThread = DeleteThread(self.mailManager, int(msgIndex))
        self.deleteThread.start()

        # Track the current timer interval with a Tk "variable"
        self._intervalDeleteEmail = IntVar(value=100)

        # Configure a timeout event (capture the ID for cancellation)
        self._afteridDeleteEmail = self._root.after(self._intervalDeleteEmail.get(), self.checkDeleteThread)


    def _newMsg(self):
        self.composeForm = ComposeForm(self, self.mailManager.userid)


    def _reply(self):
        msgIndex = self._table.getItemFocus()
        if msgIndex != "":
            msg = self.msgList[int(msgIndex)]
            self.composeForm = ComposeForm(self, self.mailManager.userid, msg.sender)
        else:
            messagebox.showinfo("Oops", "You must select a message before you can reply to it.")

    def _stop(self):
        """
        Notifies a GetMailThread or a DeleteThread that the user has requested a termination of the operation.
        """
        if self.getMailThread:
            self.getMailThread.userInterrupt = True
        elif self.deleteThread:
            self.deleteThread.userInterrupt = True


    def checkGetMailThread(self):
        """
        Called by a TKTimer. Checks the progress of a GetMailThread and updates the progress bar. When the thread is finished,
        notifies the user of failure by a messagebox or of success by inserting the mail list into the GUI.
        """
        interval = self._intervalGetEmail.get()
        if self.getMailThread.finished:
            self._root.after_cancel(self._afteridGetEmail)
            if self.getMailThread.finishCode == GetMailThread.SUCCESS:
                self.msgList = self.getMailThread.result
                for msg in self.msgList:
                    self._table.load_msg(msg)

            elif self.getMailThread.finishCode == GetMailThread.CONNECT_SUCCESS_LOGIN_FAILED:
                messagebox.showinfo("Oops", "Unable to authenticate with specified credentials.")

            elif self.getMailThread.finishCode == GetMailThread.CONNECT_FAILED:
                messagebox.showinfo("Error", "Unable to connect to specified mail server.")

            elif self.getMailThread.finishCode == GetMailThread.USER_INTERRUPT:
                print("Get interrupted")
            
            self.getMailThread = None
            
            # enable relevant widgets
            self.btn_getMail.state(["!disabled"])
            self.btn_delete.state(["!disabled"])
            self.btn_stop.state(["disabled"])
            
            # allow the progress bar's 100% phase to linger a second longer

        elif self.getMailThread.running:
            #Here I would update the progress bar if I would know how to do that
            self._afteridGetEmail = self._root.after(interval, self.checkGetMailThread)
            print("Still working")



    def checkDeleteThread(self):
        """
        Called by a Tktimer. Checks the progress of a DeleteThread and updates the status bar message. When the thread is finished,
        notifies the user of failure by a tkmessagebox or of success by removing the message from the mail list.
        """
        interval = self._intervalDeleteEmail.get()
        if self.deleteThread.finished:
            self._root.after_cancel(self._afteridDeleteEmail)
            if self.deleteThread.finishCode == DeleteThread.SUCCESS:

                self._text.delete_msg()
                self._table.delete_selected_msg()

            elif self.deleteThread.finishCode == DeleteThread.FAILURE:
                messagebox.showinfo("Failure", "Unable to delete specified message.")

            elif self.deleteThread.finishCode == DeleteThread.CONNECT_SUCCESS_LOGIN_FAILED:
                messagebox.showinfo("Oops", "Unable to authenticate with specified credentials.")

            elif self.deleteThread.finishCode == DeleteThread.CONNECT_FAILED:
                messagebox.showinfo("Error", "Unable to connect to specified mail server.")

            elif self.deleteThread.finishCode == DeleteThread.USER_INTERRUPT:
                
                print("Del interruped")

            self.deleteThread = None

            self.btn_delete.state(["!disabled"])
            self.btn_getMail.state(["!disabled"])
            self.btn_stop.state(["disabled"])

        elif self.deleteThread.running:
            self._afteridDeleteEmail = self._root.after(interval, self.checkDeleteThread)
            print("Still trying to delete")



    def run(self):
        """Run the application to termination."""
        self._root.mainloop()


class MyThread():    
    def __init__(self):
        self.userInterrupt = False # set by GUI to request an eventual shutdown of thread
        self.running = False # indicates if the thread is in progress
        self.finished = False # indicates if the thread has finished
        self.finishCode = 0 # indicate the status of the thread completion

class GetMailThread(Thread, MyThread):    
    SUCCESS, CONNECT_FAILED, CONNECT_SUCCESS_LOGIN_FAILED, USER_INTERRUPT = range(4)
    
    def __init__(self,  mailManager):
        Thread.__init__(self)
        MyThread.__init__(self)
        self.mailManager = mailManager
        self.result = []
        self.progress = 0
        self.maxProgress = 0
    
    def run(self):
        """
        Attempts to connect to POP server and download messages.
        """
        self.running = True
        connectResult = self.mailManager.connect()
        if connectResult == MailManager.CONNECT_LOGIN_SUCCESS or connectResult == MailManager.ALREADY_CONNECTED:
            nMsgs = self.mailManager.getNumMessages()
            self.maxProgress = nMsgs
            for i in range(nMsgs):
                self.progress = i
                if self.userInterrupt:
                    break
                msg = self.mailManager.getMessage(i)
                self.result.append(msg)
            self.mailManager.disconnect()
            self.finishCode = GetMailThread.SUCCESS if not self.userInterrupt else GetMailThread.USER_INTERRUPT
        elif connectResult == MailManager.CONNECT_SUCCESS_LOGIN_FAILED:
            self.finishCode = GetMailThread.CONNECT_SUCCESS_LOGIN_FAILED
        elif connectResult == MailManager.CONNECT_FAILED:
            self.finishCode = GetMailThread.CONNECT_FAILED
        
        self.finished = True
        self.running = False

class DeleteThread(Thread, MyThread):
    SUCCESS, FAILURE, CONNECT_FAILED, CONNECT_SUCCESS_LOGIN_FAILED, USER_INTERRUPT = range(5)
    
    def __init__(self,  mailManager, msgIndex):
        Thread.__init__(self)
        MyThread.__init__(self)
        self.mailManager = mailManager
        self.msgIndex = msgIndex
    
    def run(self):
        """
        Attempts to connect to POP server and delete specified message.
        """
        self.running = True
        connectResult = self.mailManager.connect()
        if connectResult == MailManager.CONNECT_LOGIN_SUCCESS or connectResult == MailManager.ALREADY_CONNECTED:
            if self.userInterrupt:
                self.finishCode = DeleteThread.USER_INTERRUPT
            elif self.mailManager.deleteMessage(self.msgIndex):
                self.finishCode = DeleteThread.SUCCESS
            else:
                self.finishCode = DeleteThread.FAILURE
            self.mailManager.disconnect()
        elif connectResult == MailManager.CONNECT_SUCCESS_LOGIN_FAILED:
            self.finishCode = DeleteThread.CONNECT_SUCCESS_LOGIN_FAILED
        elif connectResult == MailManager.CONNECT_FAILED:
            self.finishCode = DeleteThread.CONNECT_FAILED
        
        self.finished = True
        self.running = False



if __name__ == "__main__":
    MadlibApp().run()
