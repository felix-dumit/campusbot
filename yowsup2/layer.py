from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import ImageDownloadableMediaMessageProtocolEntity,MediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from ImageRecognizer import ImageRecognizer

from parse_rest.datatypes import Object
from parse_rest.datatypes import Function


getSubscribersForCategory = Function("getSubscribersForCategory")
saveNewImage = Function("saveNewImage")
userSubscribeToCategory = Function("userSubscribeToCategory")
userUnSubscribeToCategory = Function("userUnSubscribeToCategory")
userLikeImage = Function("userLikeImage")

receipt_dic = {}
ir = ImageRecognizer()

class Image(Object):
    pass



class EchoLayer(YowInterfaceLayer):

    @ProtocolEntityCallback("message")
    def onReceive(self, messageProtocolEntity):

        print messageProtocolEntity.getType()
        if messageProtocolEntity.getType() == 'text':
            self.onMessage(messageProtocolEntity)
        elif messageProtocolEntity.getType() == 'media':
            self.onMedia(messageProtocolEntity)

    @ProtocolEntityCallback("receipt")
    def onReceipt(self, entity):
        print 'onReceipt', entity.getId()
        if entity.getId() in receipt_dic:
            self.toLower(receipt_dic[entity.getId()])
        
        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", "delivery")
        self.toLower(ack)


    def onMessage(self, messageProtocolEntity):

        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), "read")

        outgoingMessageProtocolEntity = self.getResponseForTextMessage(messageProtocolEntity)

        receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt

        self.toLower(outgoingMessageProtocolEntity)


        print "Received message (%s): %s" %(messageProtocolEntity.getFrom(), messageProtocolEntity.getBody())


    def onMedia(self, messageProtocolEntity):
        print 'received media:', messageProtocolEntity

        f = messageProtocolEntity.getFrom()
        print  '-----', f
        if messageProtocolEntity.getMediaType() == "image":
            receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), "read")

            categories = ir.recognizeImage(messageProtocolEntity.getMediaUrl(),3)

            outgoingMessageProtocolEntity =  TextMessageProtocolEntity(
                'Sua mensagem foi recebida como: %s' % categories[0], to = messageProtocolEntity.getFrom())

            receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt

            self.toLower(outgoingMessageProtocolEntity)

            tags = ir.tagsForImage(messageProtocolEntity.getMediaUrl(),20)

            saveNewImage(url=messageProtocolEntity.url, jid=messageProtocolEntity.getFrom(),
                categories=categories, caption=messageProtocolEntity.getCaption(), tags=tags)

            #image = Image(url=messageProtocolEntity.url, jid=messageProtocolEntity.getFrom(), categories=categories,
            #                caption=messageProtocolEntity.getCaption(), tags=tags)
            #image.save()

            self.sendImageToSubscribers(messageProtocolEntity, categories[0])

    def sendImageToSubscribers(self, messageProtocolEntity, category):           
        debug_jids = ["5519987059806@s.whatsapp.net"]
        subscribers, shortName = getSubscribersForCategory(category=category)['result']
        print 'subscribers parse', subscribers
        subscribers = [x['username'] for x  in subscribers if x!= messageProtocolEntity.getFrom() or x in debug_jids]
        print 'subscribers',subscribers

        caption = messageProtocolEntity.getCaption() if messageProtocolEntity.getCaption() else ''

        for sub in subscribers:
            outImage = ImageDownloadableMediaMessageProtocolEntity(
                messageProtocolEntity.getMimeType(), messageProtocolEntity.fileHash, messageProtocolEntity.url, messageProtocolEntity.ip,
                messageProtocolEntity.size, messageProtocolEntity.fileName, messageProtocolEntity.encoding, messageProtocolEntity.width, messageProtocolEntity.height,
                'Nova imagem da categoria %s: %s' % (shortName, caption),
                to = str(sub), preview = messageProtocolEntity.getPreview())

            print 'enviando imagem para', sub, outImage.getId()
            self.toLower(outImage)


    def getResponseForTextMessage(self, messageProtocolEntity):
        text = messageProtocolEntity.getBody().lower()

        args = text.split(' ')

        if args[0] == 'querofotos':
            subscribed, shortName = userSubscribeToCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
            
            if subscribed:
                rsp = "Inscrito com sucesso na categoria: %s" % shortName
            else:
                rsp = "Categoria %s nao encontrada" % shortName 
            
            return TextMessageProtocolEntity(rsp,
                to = messageProtocolEntity.getFrom())

        elif args[0] == 'naoquerofotos':
            unsubscribed, shortName = userUnSubscribeToCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
            
            if unsubscribed:
                rsp = "Inscricao na categoria %s removida com sucesso" % shortName
            else:
                rsp = "Categoria %s nao encontrada" % shortName 
            
            return TextMessageProtocolEntity(rsp,
                to = messageProtocolEntity.getFrom())

        elif args[0] == 'gostei':
            liked = userLikeImage(jid=messageProtocolEntity.getFrom(), imageCode=args[1])['result'];
            if liked >=0:
                rsp = 'Imagem gostada com sucesso, total: %s gostadas' % liked
            else:
                rsp = 'Imagem com codigo %s nao encontrada' % args[1]

            return TextMessageProtocolEntity(rsp,
                to = messageProtocolEntity.getFrom())

        else:
            return TextMessageProtocolEntity(
                text,
                to = messageProtocolEntity.getFrom())


