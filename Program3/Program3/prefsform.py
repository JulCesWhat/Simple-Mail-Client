#!/usr/bin/env python3
"""GUI Example 3: Fun with the "grid" layout manager.

Also demonstrates Tk Fonts and "Variables" for data binding.
"""

from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
import mailmanager_stub as mms
from mailmanager import MailManager



# We want some bold font text...
BOLD_FONT = ("Helvetica", 12, "bold")

class PrefsForm(Toplevel):
    """Simple "login" window that prompts for username/password."""
    def __init__(self, parent, mailManager):
        """
        Constructor
        
        @param parent reference to the parent widget (QWidget)
        @param mailManager reference to the active mailManager for the program
        """
        #super().__init__()

        self.top = Toplevel()
        # We'll use Tcl/Tk "Variables" to monitor
        # the values typed into our entry boxes
        self._maserv_var = StringVar()
        self._user_var = StringVar()
        self._pass_var = StringVar()
        self.mailManager = mailManager

        Label(self.top, text="Mail server:", font=BOLD_FONT).grid(row=0, column=0)
        Label(self.top, text="Username:", font=BOLD_FONT).grid(row=1, column=0)
        Label(self.top, text="Password:", font=BOLD_FONT).grid(row=2, column=0)
        Entry(self.top, textvariable=self._maserv_var).grid(row=0, column=1)
        Entry(self.top, textvariable=self._user_var).grid(row=1, column=1)
        Entry(self.top, textvariable=self._pass_var, show="*").grid(row=2, column=1)
        Button(self.top, text="Ok", command=self._login).grid(row=3, column=0)
        Button(self.top, text="Cancel", command=self.top.destroy).grid(row=3, column=1)

        self._maserv_var.set("csunix.cs.bju.edu")
        self._user_var.set("popjwhat331")
        
    def _login(self):
        """
        Attempts a connection with POP server to verify server information and credentials. Closes the dialog on success,
        displays a QMessageBox on failure.
        """
        if self.mailManager.isConnected():
            self.mailManager.disconnect()

        self.mailManager.server = self._maserv_var.get()
        self.mailManager.userid = self._user_var.get()
        self.mailManager.passwd = self._pass_var.get()
        connectResult = self.mailManager.connect()

        if connectResult == MailManager.CONNECT_LOGIN_SUCCESS:
            print("Success")
            self.mailManager.disconnect()
            self.top.destroy()

        elif connectResult == MailManager.CONNECT_SUCCESS_LOGIN_FAILED:
            self.mailManager.disconnect()
            messagebox.showinfo("Login failed", "Server rejected specified credentials.")

        elif connectResult == MailManager.CONNECT_FAILED:
            self.mailManager.disconnect()
            messagebox.showinfo("Connect failed", "Unable to connect to specified mail server.")
