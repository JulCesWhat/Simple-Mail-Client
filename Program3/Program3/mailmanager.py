#!/usr/bin/env python3
# Filename: mailmanager.py
# Project: CpS 320 Program 3 - PyMail
# Author: Julio Cesar Whatley
# Date Last Modified: April 30 2016
# Description: Implements the MailManager and Message classes for interaction with the POP server.
#   The MailManager class is an abstraction layer between the GUI and the POP server. It connects to
#   and retrieves messages from the server. The Message class serves as an object that holds information
#   about an email message. When this script is run as the main script, several unit tests are run that
#   verify the robustness of the MailManager. The unit tests assume that the mailbox contains only email 
#   messages sent one execution of the setupmbox.py script.




from poplib import *
from time import sleep
from email import message_from_bytes

def toUtf8(byteStr):
    return byteStr.decode("utf8")


class Message():
    def __init__(self,  sender,  subject,  date,  text):
        self.sender = sender
        self.subject = subject
        self.date = date
        self.text = text


class MailManager():
    CONNECT_LOGIN_SUCCESS,  CONNECT_FAILED,  CONNECT_SUCCESS_LOGIN_FAILED, ALREADY_CONNECTED = range(4)
    """
        Attempts a connection to the POP server.
        Returns ALREADY_CONNECTED if a connection is active.
        Returns CONNECT_LOGIN_SUCCESS if connection and authentication were successful.
        Returns CONNECT_SUCCESS_LOGIN_FAILED if the connection was successful but the credentials were rejected.
        Returns CONNECT_FAILED otherwise.
    """
    def __init__(self, userid, passwd, server):
        self.userid = userid
        self.passwd = passwd
        self.server = server
        self.pop = None
        
    def connect(self):
        """
        Slot documentation goes here.
        """

        if self.isConnected():
            return MailManager.ALREADY_CONNECTED
        
        if not self.server:
            return MailManager.CONNECT_FAILED


        # attempt to establish a connection
        try:
            self.pop = POP3_SSL(self.server,  995)

        except: # catch socket errors (server unreachable) or error_proto (-ERR response)
            self.pop = None
            return MailManager.CONNECT_FAILED
        
        # attempt to authenticate
        try:
            self.pop.user(self.userid)
            self.pop.pass_(self.passwd)
        except error_proto:
            self.disconnect()
            return MailManager.CONNECT_SUCCESS_LOGIN_FAILED
        
        # return successfully
        return MailManager.CONNECT_LOGIN_SUCCESS


    def disconnect(self):
        """
        If a connection is active, signs off.
        """
        if self.isConnected():
            self.pop.quit()
            self.pop = None

    
    def isConnected(self):
        """
        Returns True if a connection is active, False otherwise.
        """
        return True if self.pop else False

    
    def getNumMessages(self):
        """
        Returns the number of messages in the mailbox if a connection is active, False otherwise.
        """
        return self.pop.stat()[0] if self.isConnected() else False

        
    def getMessage(self, msgNum):
        """
        Returns False if no connection is active.
        Returns None if unable to retrieve the specified message.
        Returns a Message object containing the requested message otherwise.
        """
        if self.isConnected():
            msgNum += 1
            if msgNum > self.getNumMessages():
                return None
                
            try:
                response = self.pop.retr(msgNum)
            except error_proto:
                return None
            
            # parse the email into a email.message.Message
            msg = message_from_bytes(b"\n".join(response[1]))
            
            # extract important headers
            sender = msg["From"] if "From" in msg else "NO SENDER"
            date = msg["Date"] if "Date" in msg else "NO DATE"
            subject = msg["Subject"] if "Subject" in msg else "NO SUBJECT"
            
            # extract message text
            # in the case of a multipart message, search for first part with content-type "text/*"
            # prefer content-type of "text/html" over "text/plain"
            if msg.is_multipart():
                text = ""
                for part in msg.get_payload():
                    if not text and part.get_content_maintype() == "text":
                        text = part.get_payload()
                        if part.get_content_subtype() == "html":
                            break
                    if text and part.get_content_type() == "text/html":
                        text = part.get_payload()
                        break
            else:
                text = msg.get_payload()
            
            # return custom Message class
            return Message(sender, subject, date, text)
        else:
            return False

        
    def deleteMessage(self, msgNum):
        """
        Returns False if no connection is active.
        Returns None if unable to delete specified message.
        Returns True if message was successfully deleted.
        """
        if self.isConnected():
            msgNum += 1
            if msgNum > self.getNumMessages():
                return None
            try:
                self.pop.dele(msgNum)
                return True
            except error_proto:
                return None
        else:
            return False 


if __name__ == "__main__":
    from sys import argv
    
    testServer = "csunix.cs.bju.edu"
    testUserid = "popjwhat331"
    testPasswd = "shishi"
    
    nArgs = len(argv)
    if nArgs > 1: testServer = argv[1]
    if nArgs > 2: testUserid = argv[2]
    if nArgs > 3: testPasswd = argv[3]
    
    testManager = MailManager(testUserid, testPasswd, testServer)
    assert testManager.connect() == MailManager.CONNECT_LOGIN_SUCCESS
    assert testManager.isConnected()
    assert testManager.getNumMessages() == 3
    
    msg = testManager.getMessage(3) # getMessage() demands a zero-based index, message #3 is out of range
    assert not msg
    
    msgs = (testManager.getMessage(0), testManager.getMessage(1), testManager.getMessage(2))
    assert msgs[0] and msgs[1] and msgs[2]
    
    for msg in msgs:
        if msg.sender == "fred@nowhere.com":
            assert msg.subject == "A word from our sponsor"
            assert msg.date
            assert msg.text == "This is a test message from fred.\n\n\nHope you like it!"
            break
    else:
        assert False # email was not in list, because break statement was not reached
    
    assert testManager.deleteMessage(1)
    assert testManager.getNumMessages() == 2
    
    msg = testManager.getMessage(1)
    assert not msg # message should have been marked for deletion and not returned
    
    testManager.disconnect()
    assert not testManager.isConnected()
    
    print("All tests passed.")