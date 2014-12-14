var ParseImage = require("parse-image");


Parse.Cloud.define("getPreviewForImageURL", function(request, response) {
    var imageURL = request.params.url;
    Parse.Cloud.httpRequest({
        url: imageURL,
        success: function(httpResponse) {
            var image = new ParseImage();
            image.setData(httpResponse.buffer).then(function(image) {
                // Crop the image to the smaller of width or height.
                var size = Math.min(image.width(), image.height());
                return image.crop({
                    left: (image.width() - size) / 2,
                    top: (image.height() - size) / 2,
                    width: size,
                    height: size
                });

            }).then(function(image) {
                // Resize the image to 64x64.
                return image.scale({
                    width: 100,
                    height: 100
                });

            }).then(function(image) {
                // Make sure it's a JPEG to save disk space and bandwidth.
                return image.setFormat("JPEG");

            }).then(function(image) {
                // Get the image data in a Buffer.
                return image.data();

            }).then(function(buffer) {
                var base64 = buffer.toString("base64");
                response.success(base64);
            });
        },
        error: function(httpResponse) {
            response.error(httpResponse.error);
        }
    });
});