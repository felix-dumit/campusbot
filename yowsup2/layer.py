#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import base64

from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import ImageDownloadableMediaMessageProtocolEntity,MediaMessageProtocolEntity
from yowsup.layers.protocol_media.protocolentities  import LocationMediaMessageProtocolEntity,MediaMessageProtocolEntity
from yowsup.layers.protocol_receipts.protocolentities  import OutgoingReceiptProtocolEntity
from yowsup.layers.protocol_acks.protocolentities      import OutgoingAckProtocolEntity
from ExternalAPI import ImageRecognizer, PlacesApi

from parse_rest.datatypes import Object
from parse_rest.datatypes import Function


getUniqueImageCategories = Function("getUniqueImageCategories")
getSubscribersForCategory = Function("getSubscribersForCategory")
saveNewImage = Function("saveNewImage")
userSubscribeToCategory = Function("userSubscribeToCategory")
userUnSubscribeToCategory = Function("userUnSubscribeToCategory")
userLikeImage = Function("userLikeImage")
retrieveImage = Function("retrieveImage")
checkInAtLocation = Function("checkInAtLocation")
changeDisplayCategory = Function("changeDisplayCategory")
checkoutAtDisplay = Function("checkoutAtDisplay")
getPreviewForImageURL = Function("getPreviewForImageURL")

PREVIEWLOCO = getPreviewForImageURL(url='http://maps.gstatic.com/mapfiles/place_api/icons/university-71.png')['result']

receipt_dic = {}
waiting_location_dic = {}

imageRecognizer = ImageRecognizer()

placesAPI = PlacesApi()
#placesAPI.searchLocation('Instituto conputacao unicamp')

result = getUniqueImageCategories()['result']
catConvert = {x['code']:x['shortName'] for x in result}

class EchoLayer(YowInterfaceLayer):

    @ProtocolEntityCallback("message")
    def onReceive(self, messageProtocolEntity):

        print messageProtocolEntity.getType(), messageProtocolEntity.getFrom()
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
        if outgoingMessageProtocolEntity:
            receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt
            self.toLower(outgoingMessageProtocolEntity)

        print "Received message (%s): %s" %(messageProtocolEntity.getFrom(), messageProtocolEntity.getBody())


    def onMedia(self, messageProtocolEntity):
        #print 'received media:', messageProtocolEntity
        #print messageProtocolEntity.getPreview()
        if messageProtocolEntity.getMediaType() == "image":
            self.onImage(messageProtocolEntity)            
        elif messageProtocolEntity.getMediaType() == 'location':
            self.onLocation(messageProtocolEntity)
           

    def onImage(self, messageProtocolEntity):
        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), "read")

        recognized_categories = imageRecognizer.recognizeImage(messageProtocolEntity.getMediaUrl(),3)

        outgoingMessageProtocolEntity =  TextMessageProtocolEntity('Sua mensagem foi recebida como: %s' % catConvert[recognized_categories[0]], to = messageProtocolEntity.getFrom())

        receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt

        self.toLower(outgoingMessageProtocolEntity)

        tags = imageRecognizer.tagsForImage(messageProtocolEntity.getMediaUrl(),20)

        image = saveNewImage(url=messageProtocolEntity.url, jid=messageProtocolEntity.getFrom(), categories=recognized_categories, 
            caption=messageProtocolEntity.getCaption(), tags=tags, mimeType=messageProtocolEntity.getMimeType(), 
            fileHash=messageProtocolEntity.fileHash, fileName=messageProtocolEntity.fileName, ip=messageProtocolEntity.ip, 
            size=messageProtocolEntity.size, encoding=messageProtocolEntity.encoding, width=messageProtocolEntity.width, 
            height=messageProtocolEntity.height, preview= base64.b64encode(messageProtocolEntity.getPreview()))['result']

        self.sendImageToSubscribers(image, catConvert[recognized_categories[0]])

    def onLocation(self, messageProtocolEntity):
        receipt = OutgoingReceiptProtocolEntity(messageProtocolEntity.getId(), messageProtocolEntity.getFrom(), "read")

        #previewStr = base64.b64encode(messageProtocolEntity.getPreview())
        if messageProtocolEntity.getFrom() in waiting_location_dic:
            if placesAPI.addLocation(waiting_location_dic[messageProtocolEntity.getFrom()], 
                messageProtocolEntity.getLatitude(), messageProtocolEntity.getLongitude()):

                outgoingMessageProtocolEntity = TextMessageProtocolEntity('Novo lugar criado com sucesso', 
                to = messageProtocolEntity.getFrom())  
            else:                   
                outgoingMessageProtocolEntity = TextMessageProtocolEntity('Erro ao criar lugar', 
                to = messageProtocolEntity.getFrom())    

            del waiting_location_dic[messageProtocolEntity.getFrom()]

        elif messageProtocolEntity.getLocationName() or messageProtocolEntity.getLocationURL():
            outgoingMessageProtocolEntity = TextMessageProtocolEntity('Por favor envie sua localização', 
                to = messageProtocolEntity.getFrom())

        else:
            code, number, time = checkInAtLocation(jid=messageProtocolEntity.getFrom(), latitude=messageProtocolEntity.getLatitude(),
                longitude=messageProtocolEntity.getLongitude())['result']

            if code == "far":
                resp = "Por favor se aproxime de um display"
            elif code == "already":
                resp = 'Você já realizou checkin no display %s, válido por mais %s segundos' % (number, time)
            elif code == "other":
                resp = 'Já existe usuário no display %s, por favor aguarde mais %s segundos' % (number, time)
            elif code == "ok":
                resp = "Realizou checkin válido por %s segundos no display %s" % (time, number)
            
            outgoingMessageProtocolEntity = TextMessageProtocolEntity(resp, to = messageProtocolEntity.getFrom())

        
        receipt_dic[outgoingMessageProtocolEntity.getId()] = receipt

        self.toLower(outgoingMessageProtocolEntity)


    def sendImageToSubscribers(self, image, category):           
        debug_jids = ["5519987059806@s.whatsapp.net", "5519982334308@s.whatsapp.net"]
        subscribers, shortName = getSubscribersForCategory(category=category)['result']
        subscribers = [x['username'] for x  in subscribers if x['username']!= image['jid']] + debug_jids

        for sub in subscribers:
            outImage = ImageDownloadableMediaMessageProtocolEntity(
                image['mimeType'], image['fileHash'], image['url'], image['ip'],
                image['size'], image['fileName'], image['encoding'], image['width'], 
                image['height'], 'Nova imagem da categoria %s (%s): %s' % (shortName, image['code'], image['caption'] or ''),
                to = str(sub), preview=image['preview'].decode('base64'))

            print 'enviando imagem para', sub, outImage.getId()
            self.toLower(outImage)


    def getResponseForTextMessage(self, messageProtocolEntity):
        text = messageProtocolEntity.getBody().lower()

        args = text.split(' ')
        args.append('')

        if args[0] == 'querofotos':
            if args[1] in catConvert.values():
                subscribed, shortName = userSubscribeToCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
            
                if subscribed:
                    rsp = "Inscrito com sucesso na categoria: %s " % shortName
                else:
                    rsp = "Erro ao se inscrever na categoria %s " % shortName 
            else:
                rsp = 'Categoria %s nao encontrada,\n categorias disponiveis: %s' % (args[1], ', '.join(sorted(catConvert.values())))
            
            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'naoquerofotos':
            if args[1] in catConvert.values():
                unsubscribed, shortName = userUnSubscribeToCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
            
                if unsubscribed:
                    rsp = "Inscricao na categoria %s removida com sucesso " % shortName
                else:
                    rsp = "Erro ao se inscrever na categoria %s " % shortName 
            else:
                rsp = 'Categoria %s nao encontrada!,\n categorias disponiveis: %s' % (args[1], ', '.join(sorted(catConvert.values())))
            
            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'gostei':
            liked = userLikeImage(jid=messageProtocolEntity.getFrom(), imageCode=args[1])['result'];
            if liked >=0:
                rsp = 'Imagem gostada com sucesso, total: %s gostada%s' % (liked, 's' if liked > 1 else '')
            else:
                rsp = 'Imagem com codigo %s nao encontrada ' % args[1]

            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'copiar':
            image = retrieveImage(imageCode=args[1])['result'];
            if image:
                return ImageDownloadableMediaMessageProtocolEntity(
                image['mimeType'], image['fileHash'], image['url'], image['ip'], image['size'], image['fileName'],
                image['encoding'], image['width'], image['height'], '%s: %s' % (image['code'], image['caption']),
                to = messageProtocolEntity.getFrom(), preview=image['preview'].decode('base64'))          
            else:
                return TextMessageProtocolEntity('Imagem com código %s nao encontrada ' % args[1], 
                    to = messageProtocolEntity.getFrom())

        elif args[0] == 'display':
            if args[1] in catConvert.values():
                status, shortName, display = changeDisplayCategory(jid=messageProtocolEntity.getFrom(), category=args[1])['result']
                if status == 'noCat':
                    rsp = 'Categoria %s nao encontrada!,\n categorias disponiveis: %s' % (args[1], ', '.join(sorted(catConvert.values())))
                elif status =='noDisplay':
                    rsp = 'Realize primeiro checkin em um display!'
                elif status == "ok":
                    rsp = 'Categoria do display %s mudada para %s' % (display, shortName)
            else:
                rsp = 'Categoria %s nao encontrada,\n categorias disponiveis: %s' % (args[1], ', '.join(sorted(catConvert.values())))
            
            return TextMessageProtocolEntity(rsp, to = messageProtocolEntity.getFrom())

        elif args[0] == 'sairdisplay':
            status, display = checkoutAtDisplay(jid=messageProtocolEntity.getFrom())['result']
            if status == 'noCheckin':
                txt = 'Voce ja nao estava em nenhum display'
            else:
                txt = 'Checkout do display %s efetuado com sucesso' % display
            return TextMessageProtocolEntity(txt, to = messageProtocolEntity.getFrom())

        elif args[0] == 'ondeeh':
            search = ' '.join(args[1:])
            location = placesAPI.searchLocation(search)
            if location:
                return LocationMediaMessageProtocolEntity(location['geometry']['location']['lat'],
                    location['geometry']['location']['lng'], location['name'].encode('utf-8'),
                    None, 'raw', to = messageProtocolEntity.getFrom())
            else:
                return TextMessageProtocolEntity('lugar %s nao encontrado' % search,
                    to = messageProtocolEntity.getFrom())

        elif args[0] == 'novolugar':
            place = ' '.join(args[1:])
            waiting_location_dic[messageProtocolEntity.getFrom()] = place
            
            return TextMessageProtocolEntity('Aguardando localização para: %s' % place,
                    to = messageProtocolEntity.getFrom())
        
        elif args[0] == 'oi':
            return TextMessageProtocolEntity('Olá do CampusBot❗',
                to = messageProtocolEntity.getFrom())
        
        else:
            txt = '''❗Comando %s nao encontrado, os possíveis comandos são:\n
→ querofotos <categoria>  - Se inscreva para receber novas fotos de uma das seguintes categorias:(pessoas, carros, flores, arquitetura, animais, natureza, comida, praia, arte, objetos, eventos, texto, pordosol)\n
→ naoquerofotos <categoria> - Cancele sua Inscricao para uma categoria\n
→ gostei <numero da foto> - Goste de uma foto indicando o numero presente no display\n
→ oi - Fale oi para o CampusBot\n
→ Envie sua localizacao para realizar checkin em um display\n
→ display <categoria> - Apos feito o checkin mude a categoria mostrada no display\n
→ sairdisplay - Libere o display para outra pessoa utilizar\n
→ Ondeeh <lugar> - Pesquise um lugar no campus\n
→ novolugar <lugar> - Crie um novo lugar no campus\n
            ''' % args[0]
            return TextMessageProtocolEntity(txt, to = messageProtocolEntity.getFrom())


