module.exports = function (context, eventGridEvent) {
    console.log('New blob notification from event grid' + eventGridEvent);
};