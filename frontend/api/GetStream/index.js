var storage = require('azure-storage')

module.exports = function (context, req) { // removed async to be able to use table api
    console.log('Querying table service');

    // load configuration stuff we need

    var account = process.env["InstanceName"];
    var accountKey = process.env["StorageAccountKey"];

    // query azure table storage

    client = storage.createTableService('DefaultEndpointsProtocol=https;AccountName=' + account + ';AccountKey=' + accountKey + ';EndpointSuffix=core.windows.net');
    
    client.retrieveEntity('files', '', 'DSCF8458', function(e,r) { 
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