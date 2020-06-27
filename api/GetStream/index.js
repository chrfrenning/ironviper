module.exports = function (context, req) {
    console.log('Querying table service');

    // load configuration stuff we need

    var account = process.env["InstanceName"];
    var accountKey = process.env["StorageAccountKey"];

    var id = req.query.id;
    var sep = id.find('-')
    var partition_key = id.split(0,sep)
    var row_key = id.split(sep+1)

    // query azure table storage

    client = storage.createTableService('DefaultEndpointsProtocol=https;AccountName=' + account + ';AccountKey=' + accountKey + ';EndpointSuffix=core.windows.net');
    
    client.retrieveEntity('files', partition_key, row_key, function(e,r) { 
        console.log("Query completed.");
        
        if ( !e )
        {
            context.res = { 
                body: r 
            };
            context.done();
        }
        else {
            context.res = {
                status: 400,
                body: "Please pass a name on the query string or in the request body"
            };
            context.done();
        }
    });
};