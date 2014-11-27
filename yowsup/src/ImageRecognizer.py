import requests



class ImageRecognizer():
    def __init__(self):
        api_key = 'acc_0d66d90a391c7ab'

        self.api_url = "http://api.imagga.com/draft/%s" + "?api_key=" + api_key

    def recognizeImage(self, url):
        classifierId = "personal_photos"
        values = "{\"urls\": \"%s\" }" % (url)
        rurl = (self.api_url % "classify/%s" % classifierId) + "&urls="+ url
        print rurl
        request = requests.post(rurl)
        res = request.json()
        
        return str(res[0]['tags'][0]['name'])

if __name__ == "__main__":
    ir = ImageRecognizer()
    ir.recognizeImage('http://playground.imagga.com/static/img/example_photo.jpg')