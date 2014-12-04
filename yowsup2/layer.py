#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import ImageDownloadableMediaMessageProtocolEntity,MediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from ImageRecognizer import ImageRecognizer

from parse_rest.datatypes import Object
from parse_rest.datatypes import Function


getUniqueImageCategories = Function("getUniqueImageCategories")
getSubscribersForCategory = Function("getSubscribersForCategory")
saveNewImage = Function("saveNewImage")
userSubscribeToCategory = Function("userSubscribeToCategory")
userUnSubscribeToCategory = Function("userUnSubscribeToCategory")
userLikeImage = Function("userLikeImage")

receipt_dic = {}
ir = ImageRecognizer()

result = getUniqueImageCategories()['result']
#[str(x['shortName']) for x in getUniqueImageCategories()['result']]
catConvert = {x['code']:x['shortName'] for x in result}

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

            recognized_categories = ir.recognizeImage(messageProtocolEntity.getMediaUrl(),3)

            outgoingMessageProtocolEntity =  TextMessageProtocolEntity(
                'Sua mensagem foi recebida como: %s' % catConvert[recognized_categories[0]], to = messageProtocolEntity.getFrom())

            receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt

            self.toLower(outgoingMessageProtocolEntity)

            tags = ir.tagsForImage(messageProtocolEntity.getMediaUrl(),20)

            saveNewImage(url=messageProtocolEntity.url, jid=messageProtocolEntity.getFrom(),
                categories=recognized_categories, caption=messageProtocolEntity.getCaption(), tags=tags)

            #image = Image(url=messageProtocolEntity.url, jid=messageProtocolEntity.getFrom(), categories=categories,
            #                caption=messageProtocolEntity.getCaption(), tags=tags)
            #image.save()

            self.sendImageToSubscribers(messageProtocolEntity, catConvert[recognized_categories[0]])

    def sendImageToSubscribers(self, messageProtocolEntity, category):           
        debug_jids = ["5519987059806@s.whatsapp.net"]
        subscribers, shortName = getSubscribersForCategory(category=category)['result']
        print 'subscribers parse', subscribers, messageProtocolEntity.getFrom()
        subscribers = [x['username'] for x  in subscribers if x['username']!= messageProtocolEntity.getFrom()] + debug_jids
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
            if args[1] in catConvert.values():
                subscribed, shortName = userSubscribeToCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
            
                if subscribed:
                    rsp = "Inscrito com sucesso na categoria: %s " % shortName
                else:
                    rsp = "Erro ao se inscrever na categoria %s ❌" % shortName 
            else:
                rsp = 'Categoria %s não encontrada❗,\n categorias disponíveis: %s' % (args[1], ', '.join(catConvert.values()))
            
            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'naoquerofotos':
            if args[1] in catConvert.values():
                unsubscribed, shortName = userUnSubscribeToCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
            
                if unsubscribed:
                    rsp = "Inscrição na categoria %s removida com sucesso " % shortName
                else:
                    rsp = "Erro ao se inscrever na categoria %s ❌" % shortName 
            else:
                rsp = 'Categoria %s não encontrada❗,\n categorias disponíveis: %s' % (args[1], ', '.join(catConvert.values()))
            
            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'gostei':
            liked = userLikeImage(jid=messageProtocolEntity.getFrom(), imageCode=args[1])['result'];
            if liked >=0:
                rsp = 'Imagem gostada com sucesso, total: %s gostada%s' % (liked, 's' if liked > 1 else '')
            else:
                rsp = 'Imagem com codigo %s não encontrada ❌' % args[1]

            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'oi':
            return TextMessageProtocolEntity('Olá do CampusBot❗',
                to = messageProtocolEntity.getFrom())
        
        else:
            txt = '''❗Comando não encontrado, os possíveis comandos são:\n
→ querofotos <categoria>  - Se inscreva para receber novas fotos de uma das seguintes categorias:(pessoas, carros, flores, arquitetura, animais, natureza, comida, praia, arte, objetos, eventos, texto, pordosol)\n
→ naoquerofotos <categoria> - Cancele sua inscrição para uma categoria\n
→ gostei <numero da foto> - Goste de uma foto indicando o numero presente no display\n
→ oi - Fale oi para o CampusBot\n
            '''
            return TextMessageProtocolEntity(txt, to = messageProtocolEntity.getFrom())


