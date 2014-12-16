import requests
import json

class ImageRecognizer():
    def __init__(self):
        api_key = 'acc_0d66d90a391c7ab'
        self.api_url = "http://api.imagga.com/draft/%s" + "?api_key=" + api_key

    def recognizeImage(self, url, num=1):
        tags = []
        i =0
        while not tags and i<5:
            i+=1
            request = requests.post(self.api_url % 'classify/personal_photos', params={"urls": url})
            res = request.json()
            print res
            tags = [str(x['name']) for x in res[0]['tags'][0:num]]
        return tags

    def tagsForImage(self, url, thresh=20):
        r = requests.get(self.api_url % 'tags', params={"url": url})
        return [str(x['tag']) for x in r.json()['tags'] if x['confidence'] > thresh]

class PlacesApi():
    def __init__(self):
        self.api_key = 'AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws'
        self.api_url = 'https://maps.googleapis.com/maps/api/place/%s/json'
    def searchLocation(self, searchString):
        s =searchString.replace(' ', '+')
        r = requests.get(self.api_url % 'nearbysearch', 
            params={
                    'location': '-22.817106,-47.069783', 'radius': 5000,
                    'keyword': s,
                    'key': self.api_key
                    }
                    )
        if r.json().get('status') == 'OK':
            return r.json().get('results')[0]
        else:
            return None

    def addLocation(self, locationName, lat, lon):
        location= {
          "location": {
            "lat": float(lat),
            "lng": float(lon)
          },
          "accuracy": 50,
          "name": locationName,
          "types": ["shoe_store"],
        }
        r = requests.post(self.api_url % 'add', params={"key":self.api_key}, data=json.dumps(location))
        print r.json()
        return r.json().get('status') == 'OK'


if __name__ == "__main__":
    ir = ImageRecognizer()
    #print ir.recognizeImage('http://playground.imagga.com/static/img/example_photo.jpg',2)    
    #print ir.tagsForImage('https://mmi203.whatsapp.net/d/D02ndanMkJDJLNxvEVbmgFR3mPQABQjd6aO8-g/AtYY_3iXKeEBeutTGOsk6YyXi7JfEdYh8f3SxqnK7qqF.jpg', 30)
    #r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json?query=XJXSKDJMXAMC&key=%s' % 'AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')
    #r = requests.get('https://maps.googleapis.com/maps/api/place/nearbysearch/json?keyword=XJXSKDJMXAMC&location=-22.817106,-47.069783&radius=5&key=%s' % 'AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')
    p = PlacesApi()
    r = p.searchLocation('XJXSKDJMXAMC')
    #r = p.addLocation('XJXSKDJMXAMC', -22.817106,-47.069783 )
    print r

    #r = requests.get('https://maps.googleapis.com/maps/api/place/radarsearch/json?location=-33.866971,-33.8669710&radius=50000000000&name=XJXSKDJMXAMC&key=AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')

    #r = requests.get('https://maps.googleapis.com/maps/api/place/details/json?placeid=qgYvCi0wMDAwMDAyZThkMDMxZTdlOjAxYjQ4Yjc1YmIzOjMwYzk4NWRkYjljMWJmZGQ&key=AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')
    #print [x['name'] for x in r.json()['results']]

    #qgYvCi0wMDAwMDAyZThkMDMxZTdlOjAxYjQ4Yjc1YmIzOjMwYzk4NWRkYjljMWJmZGQ

#{u'status': u'OK', u'scope': u'APP', u'place_id': u'qgYvCi0wMDAwMDAyZThkMDMxZTdlOjk0YzhjNmIyY2QxOjAyZTllODdiMDk5NDY5MzE', u'id': u'e2f6229a77d7081e9968228bdc4942034048f162', u'reference': u'CkQxAAAAafluG3j1_LoRf6RYd48wmib6XXHnmY5X0LZiYG36YtGyN6pB9fYYO1pi-vIRScPakHol2YpsAIVjLZQCESzWARIQ87XTISpjoNNdOvqHuz9Z2RoUP1qwhpAvKeCP8ONGFpED0FKeNBE'}


