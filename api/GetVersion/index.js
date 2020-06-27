module.exports = function (context, req) {
    console.log('Returning version number');

    context.res = { 
        body: "0.1"
    };
    
    context.done();
};