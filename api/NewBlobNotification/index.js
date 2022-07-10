module.exports = function (context, req) {
    console.log('New blob notification from event grid');

    context.res = { 
        body: "Starting extractors"
    };
    
    context.done();
};