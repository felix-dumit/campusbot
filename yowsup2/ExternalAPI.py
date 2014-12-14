import requests

class ImageRecognizer():
    def __init__(self):
        api_key = 'acc_0d66d90a391c7ab'
        self.api_url = "http://api.imagga.com/draft/%s" + "?api_key=" + api_key

    def recognizeImage(self, url, num=1):
        request = requests.post(self.api_url % 'classify/personal_photos', params={"urls": url})
        res = request.json()
        print res
        return [str(x['name']) for x in res[0]['tags'][0:num]]

    def tagsForImage(self, url, thresh=20):
        r = requests.get(self.api_url % 'tags', params={"url": url})
        return [str(x['tag']) for x in r.json()['tags'] if x['confidence'] > thresh]

class PlacesApi():
    def __init__(self):
        api_key = 'AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws'
        self.api_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json?query=%s&key=%s' % ('%s', api_key)

    def searchLocation(self, searchString):
        s =searchString.replace(' ', '+')
        r = requests.get(self.api_url % s)
        print r.json()


if __name__ == "__main__":
    ir = ImageRecognizer()
    #print ir.recognizeImage('http://playground.imagga.com/static/img/example_photo.jpg',2)    
    #print ir.tagsForImage('https://mmi203.whatsapp.net/d/D02ndanMkJDJLNxvEVbmgFR3mPQABQjd6aO8-g/AtYY_3iXKeEBeutTGOsk6YyXi7JfEdYh8f3SxqnK7qqF.jpg', 30)
    r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json?query=Instituto+Biologia+Unicamp&key=%s' % api_key)
    print r.json()['results'][0]