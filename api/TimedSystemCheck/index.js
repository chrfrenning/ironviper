const fetch = require('node-fetch');
const FormData = require('form-data');
var azure = require('azure-storage');

const MANAGEMENT_URL = "https://management.azure.com/";
var token = "";

async function getToken() 
{
    const clientId = process.env["ClientId"];
    const clientSecret = process.env["ClientSecret"];
    const tenantId = process.env["TenantId"];

    const form = new FormData();
    form.append('grant_type', 'client_credentials');
    form.append('client_id', clientId);
    form.append('client_secret', clientSecret);
    form.append('resource', MANAGEMENT_URL);

    const url = `https://login.microsoftonline.com/${tenantId}/oauth2/token`;

    const response = await fetch(url, { method: 'POST', body: form });
    const json = await response.json();

    return json.access_token;
}

async function checkQueue() {
    const instanceId = process.env["InstanceName"];
    const storageKey = process.env["StorageAccountKey"];

    var queueSvc = azure.createQueueService(instanceId, storageKey);
    
    return new Promise((resolve,reject) => {
    queueSvc.getQueueMetadata('extract-queue', (err,res) => {
        resolve(res.approximateMessageCount);
        });
    });
}

async function getInstanceState(id) {
    const apiVersionQs = '?api-version=2019-12-01';
    const headers = { 'Content-Type' : 'application/json', 'Authorization' : `Bearer ${token}` };

    var url = MANAGEMENT_URL + id + apiVersionQs;
    const response = await fetch(url, { method: 'GET', headers: headers } );
    const json = await response.json();

    return json.properties.containers[0].properties.instanceView.currentState.state;
}

async function startInstance(id) {
    console.log(`Starting instance ${id}`);

    const apiVersionQs = '?api-version=2019-12-01';
    const headers = { 'Content-Type' : 'application/json', 'Authorization' : `Bearer ${token}` };

    var url = MANAGEMENT_URL + id + "/start" + apiVersionQs;
    return new Promise((resolve) => { fetch(url, { method: 'POST', headers: headers } ) });
}

async function listInstances() {
    const subscriptionId = process.env["SubscriptionId"];
    const instanceId = process.env["InstanceName"];

    const apiVersionQs = '?api-version=2019-12-01';
    const baseUrl = `subscriptions/${subscriptionId}/resourceGroups/${instanceId}/`;
    const headers = { 'Content-Type' : 'application/json', 'Authorization' : `Bearer ${token}` };

    const response = await fetch(MANAGEMENT_URL+baseUrl+'providers/Microsoft.ContainerInstance/containerGroups/'+apiVersionQs, { method: 'GET', headers: headers } );
    const json = await response.json();

    var instances = [];
    for(n = 0; n < json.value.length; n++) 
    {
        if ( json.value[n].name.indexOf('-converter-') > 0) {
            var state = await getInstanceState(json.value[n].id);
            instances.push( { name: json.value[n].name, id: json.value[n].id, state: state } );
        }
    }

    return instances;
}

function countRunningInstances(instances)
{
    var running = 0;
    instances.forEach( i => {
        if ( i.state == "Running" )
            running++;
    });
    return running;
}

function getAvailableInstances(instances)
{
    avail = [];

    instances.forEach( i => {
        if ( i.state == "Terminated" )
            avail.push(i.id);
    });

    return avail;
}

module.exports = async function (context, myTimer) 
{
    // check if we're enabled

    if ( process.env.ConverterDisabled && process.env['ConverterDisabled'] == "true" )
    {
        context.log('Timer ran, spinning converters is disabled by config.');
        return;
    }

    // go ahead and check if we should run some containers

    var timeStamp = new Date().toISOString();
    
    if (myTimer.isPastDue)
    {
        context.log('JavaScript is running late!');
    }

    context.log('ironviper system check timer function running', timeStamp);

    var queueLength = await checkQueue();
    if ( queueLength > 0)
    {
        // We need an auth token to call into the management api's
        // A global variable for convenience

        token = await getToken();

        // Calculate how many instances we need to reach our goal of
        // processing all files within MAX_SECONDS_TO_COMPLETION

        const MAX_SECONDS_TO_COMPLETION = 120;

        secondsToCompletion = queueLength * 4; // approximate 4 seconds per file to process
        var desiredInstances = Math.min(1, secondsToCompletion / MAX_SECONDS_TO_COMPLETION);
        context.log(`Desired instances to handle queue: ${desiredInstances}`);
        
        // get the available instances

        var instances = await listInstances();
        var runningInstances = countRunningInstances(instances);
        context.log(`Currently running instances: ${runningInstances}`);
        if ( runningInstances < desiredInstances )
        {
            availableInstances = getAvailableInstances(instances);
            instancesToStart = Math.min(desiredInstances-runningInstances, availableInstances.length);
            context.log(`Available ${availableInstances.length}, attempting to start ${instancesToStart} new instances.`);
            for ( n = 0; n < instancesToStart; n++ )
            {
                // start the instance
                startInstance(availableInstances[n]);
            }
        }
    }
    else
    {
        context.log("No files in queue. All bliss.");
    }
};