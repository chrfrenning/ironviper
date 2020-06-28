var storage = require('azure-storage')

module.exports = function (context, req) {
    console.log('Direct lookup of individual file information');

    var account = process.env["InstanceName"];
    var accountKey = process.env["StorageAccountKey"];

    var id = req.query.id;
    
    var sep = id.indexOf('-')
    var partition_key = id.slice(0,sep)

    console.log('Id: ' + id + ', partition_key: ' + partition_key)

    // query azure table storage

    client = storage.createTableService('DefaultEndpointsProtocol=https;AccountName=' + account + ';AccountKey=' + accountKey + ';EndpointSuffix=core.windows.net');
    
    client.retrieveEntity('files', partition_key, id, function(e,r) { 
        
        if ( !e )
        {
            context.res = { 
                body: r 
            };
            context.done();
        }
        else {
            console.log(e);

            context.res = {
                status: 400,
                body: "Resource not found."
            };
            context.done();
        }
        
    });
};