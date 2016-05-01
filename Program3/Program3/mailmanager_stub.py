# Filename: mailmanager_stub.py
# Project: CpS 320 Program 3 - PyMail
# Author: Julio Cesar Whatley
# Date Last Modified: April 30 2016
# Description: Implements the MailManager and Message classes for testing purposes.
#   The MailManager class does not connect to a real POP server but can be used for simulation
#   purposes in the event that no POP server is available.


class Message():
    def __init__(self,  sender,  subject,  date,  text):
        self.sender = sender
        self.subject = subject
        self.date = date
        self.text = text


class MailManager():
    CONNECT_LOGIN_SUCCESS,  CONNECT_FAILED,  CONNECT_SUCCESS_LOGIN_FAILED = range(3)
    
    def __init__(self, userid, passwd, server):
        self.userid = userid
        self.passwd = passwd
        self.server = server
        self.msgList = [
            Message("from field 1",  "to field 1",  "subject 1",  "contents 1"), 
            Message("from field 2",  "to field 2",  "subject 2",  "contents 2"), 
            Message("from field 3",  "to field 3",  "subject 3",  "contents 3"), 
        ];
        
    
    def connect(self):
        if self.userid == "fred" and self.passwd == "yes":
            return MailManager.CONNECT_LOGIN_SUCCESS
        else:
            return MailManager.CONNECT_SUCCESS_LOGIN_FAILED

    
    def disconnect(self):
        pass

    
    def isConnected(self):
        return True

    
    def getNumMessages(self):
        return len(self.msgList)

    
    def getMessage(self,  msgNum):
        return self.msgList[msgNum]

    
    def deleteMessage(self,  msgNum):
        if msgNum > (len(self.msgList) - 1):
            return None
        else:
            del self.msgList[msgNum]
            return True
