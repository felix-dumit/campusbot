var _ = require('underscore');
var Image = Parse.Object.extend("Image");
var Category = Parse.Object.extend("Categories");
var Buffer = require('buffer').Buffer;


Parse.Cloud.define("getUniqueImageCategories", function(request, response) {
    Parse.Cloud.useMasterKey();
    
    var query = new Parse.Query(Category);
    query.find().then(function(cats){
        response.success(cats);
    }, function(error){
        response.error(error);
    });
    /*
    var query = new Parse.Query(Image);
    var allCats = [];
    query.find().then(function(images) {
        _.each(images, function(image) {
            allCats = _.union(allCats, image.get('categories'))
        });
        response.success(_.uniq(allCats));
    }, function(error) {
        reponse.error(error);

    });
    */
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

