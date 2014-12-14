import requests
import json

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
        self.api_key = 'AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws'
        self.api_url = 'https://maps.googleapis.com/maps/api/place/%s/json'
    def searchLocation(self, searchString):
        s =searchString.replace(' ', '+')
        r = requests.get(self.api_url % 'textsearch', 
            params={
                    'location': '-22.817106,-47.069783', 'radius': 5000,
                    'query': s,
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
    #r = requests.get('https://maps.googleapis.com/maps/api/place/textsearch/json?query=XJXSKD+10&key=%s' % 'AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')
    p = PlacesApi()
    #r = p.searchLocation('XJXSKDJMXAMC')
    r = p.addLocation('XJXSKDJMXAMC', -33.8669710,-33.8669710 )
    print r

    #r = requests.get('https://maps.googleapis.com/maps/api/place/radarsearch/json?location=-33.866971,-33.8669710&radius=50000000000&name=XJXSKDJMXAMC&key=AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')

    #r = requests.get('https://maps.googleapis.com/maps/api/place/details/json?placeid=qgYvCi0wMDAwMDAyZThkMDMxZTdlOjAxYjQ4Yjc1YmIzOjMwYzk4NWRkYjljMWJmZGQ&key=AIzaSyDK3VO6SIMpZEfi3djccBETdf-mv9Ccfws')
    #print r.json()

    #qgYvCi0wMDAwMDAyZThkMDMxZTdlOjAxYjQ4Yjc1YmIzOjMwYzk4NWRkYjljMWJmZGQ



