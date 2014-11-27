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

import os
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.sys.path.insert(0,parentdir)
import datetime, sys

if sys.version_info >= (3, 0):
    raw_input = input

from Yowsup.connectionmanager import YowsupConnectionManager
from Yowsup.Media.downloader import MediaDownloader
from Yowsup.Media.uploader import MediaUploader

class Responder:
    
    def __init__(self, queue, image_queue, keepAlive = True, sendReceipts = True):
        self.sendReceipts = sendReceipts
        
        connectionManager = YowsupConnectionManager()
        connectionManager.setAutoPong(keepAlive)

        self.signalsInterface = connectionManager.getSignalsInterface()
        self.methodsInterface = connectionManager.getMethodsInterface()
        
        self.signalsInterface.registerListener("message_received", self.onMessageReceived)
        self.signalsInterface.registerListener("auth_success", self.onAuthSuccess)
        self.signalsInterface.registerListener("auth_fail", self.onAuthFailed)
        self.signalsInterface.registerListener("disconnected", self.onDisconnected)
        self.signalsInterface.registerListener("message_error", self.onError)

        self.signalsInterface.registerListener("receipt_messageSent", self.onMessageSent)
        self.signalsInterface.registerListener("receipt_messageDelivered", self.onMessageDelivered)
        self.signalsInterface.registerListener("image_received", self.onImageReceived)


        
        self.cm = connectionManager

        self.queue = queue
        self.image_queue = image_queue

        self.reply_dic = {}

        self.running = True
    
    def login(self, username, password):
        self.username = username
        self.methodsInterface.call("auth_login", (username, password))

    def sendMessage(self, jid, message, replyMsg=None):
        msgId = self.methodsInterface.call("message_send", (jid, message))

        if replyMsg:
            self.reply_dic[msgId] = replyMsg

    def sendImage(self, jid, url, name, size, preview="yes"):
        print("Sending message_image")
        msgId = self.methodsInterface.call("message_imageSend", (jid, url, name, size, preview))
        #self.sentCache[msgId] = [int(time.time()), self.path]

    def sendLocation(self, jid, name, lat, lon):
        print("Sending message_location")
        
        msgId = self.methodsInterface.call("message_locationSend", (jid, lat, lon, name))      
        #self.sentCache[msgId] = [int(time.time()), self.path]

    def onAuthSuccess(self, username):
        print("Authed %s" % username)
        self.methodsInterface.call("ready")

    def onAuthFailed(self, username, err):
        print("Auth Failed!")

    def onDisconnected(self, reason):
        print("Disconnected because %s" %reason)
        #exit(1)
        self.running = False    
    def onError(self, msgId, jid, errorCode):
        print "ERRO:", msgId, jid, errorCode

    def onMessageReceived(self, messageId, jid, messageContent, timestamp, wantsReceipt, pushName, isBroadCast):
        formattedDate = datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y %H:%M')
        print("%s [%s]:%s"%(jid, formattedDate, messageContent))

        self.queue.put([jid, messageContent, messageId])

        #if self.sendReceipts and wantsReceipt:
        #self.methodsInterface.call("message_ack", (jid, messageId))

    #new media functions
    #def onImageReceived(self,msgId, jid, preview, url, size, caption, wantsReceipt, pushName, timestamp, isBroadcast):
    def onImageReceived(self, msgId, jid, preview, url, size, wantsReceipt, isBroadcast):

        print("Image received: Id:%s Jid:%s Url:%s size:%s caption:%s pushName:%s" %(msgId, jid, url, size, "", ""))
        
        self.image_queue.put([jid, msgId, preview, url, size, "", ""])
        #downloader = MediaDownloader(self.onDlsuccess, self.onDlerror, self.onDlprogress)
        #downloader.download(url)
        
        #if self.sendReceipts and wantsReceipt:
        #self.methodsInterface.call("message_ack", (jid, msgId))

        #timeout = 10
        #t = 0;
        #while t < timeout:
        #    time.sleep(0.5)
        #    t+=1

    def onDlsuccess(self, path):
        stdout.write("\n")
        stdout.flush()
        print("Image downloded to %s"%path)
        print(self.getPrompt())

    def onDlerror(self):
        stdout.write("\n")
        stdout.flush()
        print("Download Error")
        print(self.getPrompt())

    def onDlprogress(self, progress):
        stdout.write("\r Progress: %s" % progress)
        stdout.flush()



    def onMessageSent(self, jid, msgId):
        print "message sent to", jid, msgId

        if msgId in self.reply_dic:
            self.methodsInterface.call("message_ack", (jid, self.reply_dic[msgId]))
            del self.reply_dic[msgId]


    def onMessageDelivered(self, jid, msgId):
        print "message delivered to", jid, msgId

    