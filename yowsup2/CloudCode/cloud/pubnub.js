var pubnub = {
    publish_key: 'pub-c-6184d710-7487-4b8f-babf-d83356e499da',
    subscribe_key: 'sub-c-f65415a2-7c27-11e4-b197-02ee2ddab7fe'
};

exports.sendMessageToChannel = function(channel, message) {

    var promise = new Parse.Promise();

    Parse.Cloud.httpRequest({
        url: 'http://pubsub.pubnub.com/publish/' +
            pubnub.publish_key + '/' +
            pubnub.subscribe_key + '/0/' +
            channel + '/0/' +
            encodeURIComponent(JSON.stringify(message)),

        // SUCCESS CALLBACK
        success: function(httpResponse) {
            console.log('PUBNUB MANDOUR PRO: ' + channel);
            // console.log(httpResponse.text);
            // httpResponse.text -> [1,"Sent","14090206970886734"]            
            promise.resolve();
        },
        // You should consider retrying here when things misfire
        error: function(httpResponse) {
            console.error('Request failed ' + httpResponse.status);
            promise.reject();
        }
    });

    return promise;
    //- See more at: http://www.pubnub.com/blog/realtime-collaboration-sync-parse-api-pubnub/#sthash.ucaSiwJQ.dpuf

}