var storage = require('azure-storage');
const { TableQuery, TableService } = require('azure-storage');
const azurestorage = require('azure-storage');

module.exports = function (context, req) {
    console.log('Querying table service for latest files');

    // load configuration stuff we need

    var account = process.env["InstanceName"];
    var accountKey = process.env["StorageAccountKey"];

    // query azure table storage

    client = storage.createTableService('DefaultEndpointsProtocol=https;AccountName=' + account + ';AccountKey=' + accountKey + ';EndpointSuffix=core.windows.net');

    var tableQuery = new storage.TableQuery().top(200).select('RowKey', 'name', 'ext', 'url', 'pvs');
        
    client.queryEntities('files', tableQuery, null, function(e,r) {
        console.log("Query completed.");

        if ( !e )
        {
            context.res = { 
                body: r.entries 
            };
            context.done();
        }
        else {
            context.res = {
                status: 500,
                body: "Can not query files collection."
            };
            context.done();
        }
    } 
    );

};