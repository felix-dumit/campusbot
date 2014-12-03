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


if __name__ == "__main__":
    ir = ImageRecognizer()
    #print ir.recognizeImage('http://playground.imagga.com/static/img/example_photo.jpg',2)    
    print ir.tagsForImage('https://mmi203.whatsapp.net/d/D02ndanMkJDJLNxvEVbmgFR3mPQABQjd6aO8-g/AtYY_3iXKeEBeutTGOsk6YyXi7JfEdYh8f3SxqnK7qqF.jpg', 30)



    ["text_visuals", "macro_flowers", "cars_vehicles", "people_portraits", 
"food_drinks", "pets_animals", "interior_objects", "events_parties", 
"streetview_architecture", "sunrises_sunsets", "nature_landscape", "paintings_art", 
"beaches_seaside"]