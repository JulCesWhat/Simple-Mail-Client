#!/usr/bin/env python3

# -*- coding: utf-8 -*-
# Filename: composeform.py
# Project: CpS 320 Program 3 - PyMail
# Author: Julio Cesar Whatley
# Date Last Modified: April 30 2016
# Description: Implements the event handlers of the ComposeForm.
#   The ComposeForm allows the user to compose and send new messages and
#   reply to messages in his mailbox.

"""Program 3: Mail composition window
"""
from tkinter import *
from tkinter.ttk import *
from tkinter import messagebox
# Import Tk standard dialogs
from tkinter import filedialog

from email.message import Message
import smtplib
import mailmanager_stub as mms

import re, sys, os
from smtplib import SMTP, SMTPException
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.utils import formatdate
from email.encoders import encode_base64
from mailmanager import Message


# Use the local MTA (mail transfer agent) on csunix
SMTP_HOST = "localhost"

class ComposeForm(Toplevel):
    """Email composition window class.

    Subclasses Tk's "Toplevel" widget class and handles all
    email sending logic (remember, this will probably work
    best/only on csunix).
    """
    def __init__(self, parent, sender_email, receiver_email="", smtp_host="SMTP_HOST"):#(self, parent, userid, replyMsg = None)
        """Construct composition window.

        Arguments:
          * sender_email: what to put in the "From" header
          * smtp_host: what SMTP server to use for sending mail (optional)
        """
        super().__init__()
        self.title("Compose Message")

        self.attachments = []

        self._sender_email = sender_email
        self._smtp_host = smtp_host

        self._to_var = StringVar()
        self._subject_var = StringVar()

        # Top panel of interface, containing buttons
        btns = Frame(self)
        self._bsend = Button(btns, text="Send",
                             underline=0, command=self._send)
        self._bclose = Button(btns, text="Close",
                              underline=0, command=self._close)
        self._battachment = Button(btns, text="Attachemt",
                              underline=0, command=self._addAttachemt)

        self._bsend.pack(side=LEFT, padx=3, pady=3)
        self._bclose.pack(side=LEFT, padx=3, pady=3)
        self._battachment.pack(side=RIGHT, padx=3, pady=3)


        # Middle panel of interface, containing header entry fields
        hdrs = Frame(self)
        Label(hdrs, text="To:").grid(
            row=0, column=0, sticky="W", padx=3, pady=3)
        Label(hdrs, text="Subject:").grid(
            row=1, column=0, sticky="W", padx=3, pady=3)
        Entry(hdrs, textvariable=self._to_var).grid(
            row=0, column=1, sticky="NESW", padx=3, pady=3)
        Entry(hdrs, textvariable=self._subject_var).grid(
            row=1, column=1, sticky="NESW", padx=3, pady=3)
        hdrs.grid_columnconfigure(1, weight=1)

        self._to_var.set(receiver_email)
       
        # "Stretchy" middle of composition window: a scrolling text field
        tframe = Frame(self)
        self._text = Text(tframe, wrap="word")
        scrolly = Scrollbar(tframe, orient=VERTICAL, command=self._text.yview)
        self._text["yscrollcommand"] = scrolly.set
        scrolly.pack(side=RIGHT, fill=Y)
        self._text.pack(expand=YES, fill=BOTH, padx=3, pady=3)

        # "Status" bar at bottom
        self._status = Label(self)

        # Pack the "fixed" parts of the UI
        btns.pack(side=TOP, fill=X)
        hdrs.pack(side=TOP, fill=X)
        self._status.pack(side=BOTTOM, fill=X)

        # Pack the text frame LAST, to make it the stretchy part
        tframe.pack(expand=YES, fill=BOTH)

    def _send(self):
        # An exercise for the reader: parse multiple email address from the "To" field
        to_addr = self._to_var.get().strip()
        if not to_addr:
            messagebox.showerror(title="Uh-oh", message="You must provide a 'To' email address!")

        msg = MIMEMultipart()
        msg['From'] = self._sender_email
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self._subject_var.get()
        msg.attach(MIMEText(self._text.get('1.0', END)))

        for f in self.attachments:
        	part = MIMEBase('application', "octet-stream")
        	part.set_payload(open(f,"rb").read())
        	encode_base64(part)
        	part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        	msg.attach(part)

        mta = None
        try:
        	#POP3_SSL(self.server,  995)
            mta = smtplib.SMTP("smtp.bju.edu")
            mta.sendmail(self._sender_email + '@bju.edu', [to_addr], msg.as_string())
            mta.close()
            self.destroy()

        except SMTPException as ex:
            messagebox.showerror(title="Uh-oh", message="Something went wrong: " + str(ex))

    def _close(self):
        # Hope they wanted to do that...
        self.destroy()

    def _addAttachemt(self):
    	file = filedialog.askopenfilename()
    	if file:
    		self.attachments.append(file)

def main(sender=""):
    import getpass
    print(sender)
    win = ComposeWindow(sender)
    Style(win).theme_use("clam")
    win.wait_window()

if __name__ == "__main__":
	main()