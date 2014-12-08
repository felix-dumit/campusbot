var _ = require('underscore');
var Image = Parse.Object.extend("Image");
var Category = Parse.Object.extend("Categories");
var Display = Parse.Object.extend("Display");
var Buffer = require('buffer').Buffer;
var PUBNUB = require('cloud/pubnub');


Parse.Cloud.define("getUniqueImageCategories", function(request, response) {
    Parse.Cloud.useMasterKey();
    
    var query = new Parse.Query(Category);
    query.addAscending('shortName');
    query.find().then(function(cats){
        response.success(cats);
    }, function(error){
        response.error(error);
    });
});

Parse.Cloud.define("getSubscribersForCategory", function(request, response) {

    Parse.Cloud.useMasterKey();

    var category = request.params.category;

    var query = new Parse.Query(Category);
    query.equalTo('shortName', category);
    query.include('subscribers');
    query.first().then(function(cat) {
        if (!cat) {
            response.success([[],'']);
        } else {
            console.log('subscribers:' + cat.get('subscribers').length);
            response.success([cat.get('subscribers'), cat.get('shortName')]);
        }
    }, function(error) {
        response.error(error);
    });
});


var categoryForCodes = function(codes) {
    var promises = [];
    var cats = [];
    _.each(codes, function(code) {
        var query = new Parse.Query(Category);
        query.equalTo('code', code);
        query.include('subscribers');
        promises.push(query.first().then(function(cat) {
            if (cat) {
                cats.push(cat);
            } else {
                cat = new Category();
                cat.set('subscribers', []);
                cat.set('code', code);
                cat.set('name', 'Outras');
                cat.save().then(function(savedCat) {
                    cats.push(cat);
                });
            }
        }));
    });

    var promise = new Parse.Promise();

    Parse.Promise.when(promises).then(function(categories) {
        promise.resolve(cats);
    });
    return promise;

}

var userForJID = function(jid) {

    var promise = new Parse.Promise();
    var query = new Parse.Query(Parse.User);
    query.equalTo('username', jid);
    query.first().then(function(user) {
        if (user) {
            promise.resolve(user);
            return;
        }
        user = new Parse.User();

        var password = new Buffer(24);
        _.times(24, function(i) {
            password.set(i, _.random(0, 255));
        });
        user.set("username", jid);
        user.set("password", password.toString('base64'));
        user.signUp().then(function(user) {
            promise.resolve(user);
        }, function(error) {
            promise.reject(user);
        });

    }, function(error) {
        console.log("USER FIND ERROR " + JSON.stringify(error));
        return error;
    });

    return promise;
}

Parse.Cloud.define("saveNewImage", function(request, response) {
    Parse.Cloud.useMasterKey();

    console.log('HERE:' + request.params.preview);

    var query = new Parse.Query(Image);
    query.equalTo('url', request.params.url);

    var countQuery = new Parse.Query(Image);

    query.first().then(function(image) {
        return image || new Image();
    }).then(function(image) {
        image.set('url', request.params.url);
        image.set('caption', request.params.caption);
        image.set('tags', request.params.tags);
        image.set('jid', request.params.jid);
        image.set('raw_categories', request.params.categories);
        image.set('width', request.params.width);
        image.set('height', request.params.height);
        image.set('mimeType', request.params.mimeType);
        image.set('fileHash', request.params.fileHash);
        image.set('fileName', request.params.fileName);
        image.set('ip', request.params.ip);
        image.set('size', request.params.size);
        image.set('encoding', request.params.encoding);
        image.set('preview', request.params.preview);

        newImage = image;
        return Parse.Promise.when(image,
            userForJID(request.params.jid),
            categoryForCodes(request.params.categories),
            countQuery.count()
        );
    }).then(function(image, user, categories, count) {
        image.set('user', user);
        image.set('categories', categories);
        image.set('category', categories[0]);
        image.set('code', ('00000' + count).substr(-5));
        return image.save();
    }).then(function(image) {
        response.success(image);
    }, function(error) {
        response.error(error);
    });

});



Parse.Cloud.define("userSubscribeToCategory", function(request, response) {
    var shortName = request.params.category;
    var jid = request.params.jid;

    var query = new Parse.Query(Category);
    query.equalTo('shortName', shortName);

    Parse.Promise.when(query.first(), userForJID(jid)).then(function(category, user) {
        category.addUnique('subscribers', user);
        return category.save()
    }).then(function(savedCategory) {
        response.success([true, shortName]);
    }, function(error) {
        response.success([false, shortName]);
    });

});

Parse.Cloud.define("userUnSubscribeToCategory", function(request, response) {
    var shortName = request.params.category;
    var jid = request.params.jid;

    var query = new Parse.Query(Category);
    query.equalTo('shortName', shortName);

    Parse.Promise.when(query.first(), userForJID(jid)).then(function(category, user) {
        category.remove('subscribers', user);
        return category.save()
    }).then(function(savedCategory) {
        response.success([true, shortName]);
    }, function(error) {
        response.success([false, shortName]);
    });

});


Parse.Cloud.define("userLikeImage", function(request, response){
	var jid = request.params.jid;
	var imageCode = request.params.imageCode;

	var query = new Parse.Query(Image);
	query.equalTo('code', imageCode);

	Parse.Promise.when(query.first(), userForJID(jid)).then(function(image, user){
		if(!image){
			return -1;
		}
		image.addUnique('likers', user);
		return image.save().then(function(image){
            return image.get('likers').length;
        });
	}).then(function(c){
		response.success(c);
	}, function(error){
		response.error(error);
	});
});


Parse.Cloud.define("retrieveImage", function(request, response){
    var imageCode = request.params.imageCode;

    var query = new Parse.Query(Image);
    query.equalTo('code', imageCode);

    query.first().then(function(image){
        response.success(image);
    }, function(error){
        response.error(error);
    });
});



var checkTime = 60000;

Parse.Cloud.define("checkInAtLocation", function(request, response){
    var lat = parseFloat(request.params.latitude);
    var lon = parseFloat(request.params.longitude);
    var jid = request.params.jid;

    var query = new Parse.Query(Display);
    var point = new Parse.GeoPoint({latitude:lat, longitude:lon});
    query.withinKilometers('location', point, 1);
    Parse.Promise.when(query.first(), userForJID(jid)).then(function(display, user){
        if(!display){
            return ["far", 0, 0];
        }
        var now = new Date();
        var timeDiff = now - display.get('lastDate');
        // existe usuario que fez checkin
        if(display.get('user') && timeDiff < checkTime){
            if(display.get('user').id == user.id){
                return ["already", display.get('number'), parseInt((checkTime-timeDiff)/1000)];
            }
            else{
                return ["other", display.get('number'), parseInt((checkTime-timeDiff)/1000)];
            }
        }
        else{
            display.set('user', user);
            display.set('lastDate', now);
            return display.save().then(function(savedDisplay){
                return ["ok", savedDisplay.get('number'), 60];
            });
        }

    }).then(function(rsp){
        response.success(rsp);
    }, function(error){
        response.error(error);
    });

});


Parse.Cloud.define("changeDisplayCategory", function(request, response){
    var shortName = request.params.category;
    var jid = request.params.jid;

    var query = new Parse.Query(Category);
    query.equalTo('shortName', shortName);

    Parse.Promise.when(query.first(), userForJID(jid)).then(function(category, user) {
        if(!category){
            return ["noCat", shortName, -1]
        }
        var query = new Parse.Query(Display);
        query.equalTo('user', user);
        return query.first().then(function(display){
            var now = new Date();
            var timeDiff = now - display.get('lastDate');
            if(display && timeDiff < checkTime){
                var channel = 'display' + display.get('number');
                return PUBNUB.sendMessageToChannel(channel, {category: category})
                .then(function(){
                    return ["ok", shortName, display.get('number')];
                });
            }
            else{
                return ["noDisplay", shortName, 0]
            }
        });
    }).then(function(rsp){
        response.success(rsp);
    }, function(error){
        response.error(error);
    });
})

