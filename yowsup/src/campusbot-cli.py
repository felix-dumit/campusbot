#!/usr/bin/python

'''
Copyright (c) <2012> Tarek Galal <tare2.galal@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this 
software and associated documentation files (the "Software"), to deal in the Software 
without restriction, including without limitation the rights to use, copy, modify, 
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to 
permit persons to whom the Software is furnished to do so, subject to the following 
conditions:

The above copyright notice and this permission notice shall be included in all 
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR 
A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

__author__ = "Tarek Galal"
__version__ = "0.41"
__email__ = "tare2.galal@gmail.com"
__license__ = "MIT"

import argparse, sys, os, csv
from Yowsup.Common.utilities import Utilities
from Yowsup.Common.debugger import Debugger
from Yowsup.Common.constants import Constants
from Examples.Responder import Responder
from Queue import Queue
from ImageRecognizer import ImageRecognizer

import threading,time, base64

DEFAULT_CONFIG = "zapzap.config"
COUNTRIES_CSV = "countries.csv"

def getCredentials(config = DEFAULT_CONFIG):
    if os.path.isfile(config):
        f = open(config)
        
        phone = ""
        idx = ""
        pw = ""
        cc = ""
        
        try:
            for l in f:
                line = l.strip()
                if len(line) and line[0] not in ('#',';'):
                    
                    prep = line.split('#', 1)[0].split(';', 1)[0].split('=', 1)
                    
                    varname = prep[0].strip()
                    val = prep[1].strip()
                    
                    if varname == "phone":
                        phone = val
                    elif varname == "id":
                        idx = val
                    elif varname =="password":
                        pw =val
                    elif varname == "cc":
                        cc = val

            return (cc, phone, idx, pw);
        except:
            pass

    return 0

def dissectPhoneNumber(phoneNumber):
    try:
        with open(COUNTRIES_CSV, 'r') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            for row in reader:
                if len(row) == 3:
                    country, cc, mcc = row
                else:
                    country,cc = row
                    mcc = "000"
                try:
                    if phoneNumber.index(cc) == 0:
                        print("Detected cc: %s"%cc)
                        return (cc, phoneNumber[len(cc):])

                except ValueError:
                    continue
                
    except:
        pass
    return False


class ThreadedCampusBot():
    def __init__(self):
        credentials = getCredentials(DEFAULT_CONFIG)
        countryCode, login, identity, password = credentials
        identity = Utilities.processIdentity(identity)
        password = base64.b64decode(bytes(password.encode('utf-8')))
        dissected = dissectPhoneNumber(login)
        countryCode, phoneNumber = dissected
        Debugger.enabled = False

        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()        
        self.incoming_image_queue = Queue()
        self.outgoing_image_queue = Queue()

        self.wa = Responder(self.incoming_queue, self.incoming_image_queue, True, True)
        self.wa.login(login, password)

        self.ir = ImageRecognizer()

        t = threading.Thread(target=self.listen_worker)
        t.setDaemon(True)
        t.start()

        t = threading.Thread(target=self.send_worker)
        t.setDaemon(True)
        t.start()

        t = threading.Thread(target=self.listen_image_worker)
        t.setDaemon(True)
        t.start()

        t = threading.Thread(target=self.send_image_worker)
        t.setDaemon(True)
        t.start()

        #self.wa.sendMessage("5519987059806@s.whatsapp.net", "mensage")
        # self.wa.sendImage("5519987059806@s.whatsapp.net", 'https://mmi202.whatsapp.net/d/CL_rmBHbf2zN7eveJAybclR3NxQABQjYFCz-IA/As27Ab_T5VQdV3q5ORfNadEbC5n8w9SB9uSZZs811e_u.jpg', 'image.jpg', '145800',
        # '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')
        # self.wa.sendMessage("5519987059806@s.whatsapp.net", "mensagem 2")

        #self.wa.sendLocation("5519987059806@s.whatsapp.net", "nome", '-22.8233998', '-47.0748121')
        while self.wa.running:
            pass
        exit(1)
            

    def listen_worker(self):
        while True:
            jid, message, msgId = self.incoming_queue.get()            
            self.outgoing_queue.put([jid, message, msgId])
            self.incoming_queue.task_done()

    def send_worker(self):
        while True:
            jid, message, msgId = self.outgoing_queue.get()
            self.wa.sendMessage(jid, message,replyMsg=msgId)
            self.outgoing_queue.task_done()

    def listen_image_worker(self):
        while True:

            jid, msgId, preview, url, size, caption, pushName = self.incoming_image_queue.get()
            
            response = self.ir.recognizeImage(url)
            print response
            self.wa.sendMessage(jid, response, replyMsg=msgId)
            #self.wa.sendImage(jid, url, "image.jpg", size, preview)
            #self.outgoing_queue.put(x)
            self.incoming_image_queue.task_done()

    def send_image_worker(self):
        while True:
            jid, messageId, preview, url, size = self.outgoing_image_queue.get()
            #print "aqui", jid, message
            self.wa.sendMessage(jid, "to te mandando imagem")
            #self.wa.sendImage(jid, url, "nome.jpg", size, preview)
            self.outgoing_image_queue.task_done()


if __name__ == "__main__":
    bot = ThreadedCampusBot()  











