from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import ImageDownloadableMediaMessageProtocolEntity,MediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from ImageRecognizer import ImageRecognizer

from parse_rest.datatypes import Object


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

        if entity.getId() in receipt_dic:
            self.toLower(receipt_dic[entity.getId()])

        ack = OutgoingAckProtocolEntity(entity.getId(), "receipt", "delivery")
        self.toLower(ack)


    def onMessage(self, messageProtocolEntity):

        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())

        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
            messageProtocolEntity.getBody(),
            to = messageProtocolEntity.getFrom())

        receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt

        self.toLower(outgoingMessageProtocolEntity)


        print "Received message (%s): %s" %(messageProtocolEntity.getFrom(), messageProtocolEntity.getBody())



    # def __init__(self,
    #         mediaType, mimeType, fileHash, url, ip, size, fileName,
    #         encoding, width, height,
    #         _id = None, _from = None, to = None, notify = None, timestamp = None, participant = None,
    #         preview = None, offline = None, retry = None):
    def onMedia(self, messageProtocolEntity):
        print 'received media:', messageProtocolEntity

        print  '-----'

        print messageProtocolEntity.getFrom()

        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom())

        # outImage = ImageDownloadableMediaMessageProtocolEntity(messageProtocolEntity.getMediaType(),
        #     messageProtocolEntity.getMimeType(), messageProtocolEntity.fileHash, messageProtocolEntity.url, messageProtocolEntity.ip,
        #     messageProtocolEntity.size, messageProtocolEntity.fileName, messageProtocolEntity.encoding, messageProtocolEntity.width, messageProtocolEntity.height,
        #     to=messageProtocolEntity.getFrom())
        
        categories = ir.recognizeImage(messageProtocolEntity.getMediaUrl(),3)


        outgoingMessageProtocolEntity = TextMessageProtocolEntity(
            ', '.join(categories), to = messageProtocolEntity.getFrom())

        receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt
        #receipt_dic[outImage.getId()] = receipt

        self.toLower(outgoingMessageProtocolEntity)
        #self.toLower(outImage)

        image = Image(url=messageProtocolEntity.url, jid=messageProtocolEntity.getFrom(), categories=categories)
        image.save()




