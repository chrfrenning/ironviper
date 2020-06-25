var storage = require('azure-storage')

module.exports = function (context, req) { // removed async to be able to use table api
    console.log('Querying table service');

    client = storage.createTableService('DefaultEndpointsProtocol=https;AccountName=ironviper00b6e128;AccountKey=FXIAyF/d8IczfJNHZ1EO+zi3rQeXOc8sKOJtVRnkYdfWiHcqXZdEeH2hWZ3whmDhBrhWQqd/h509p11R7HQdOw==;EndpointSuffix=core.windows.net');
    
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