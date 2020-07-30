# Sets up the current branch for local debugging
# and starts azure functions and live-server

# Get settings
echo "Loading configuration..."

rgn=$(./tools/getsetting.py instance_name)
storageKey=$(./tools/getsetting.py account_key)
registryUrl=$(./tools/getsetting.py registry_url)
registryUsername=$(./tools/getsetting.py registry_username)
registryPassword=$(./tools/getsetting.py registry_password)
staticurl=$(./tools/getsetting.py static_url)
functionsurl=$(./tools/getsetting.py functions_url)
clientId=$(./tools/getsetting.py client_id)
clientSecret=$(./tools/getsetting.py client_secret)
tenantId=$(./tools/getsetting.py tenant_id)
subscriptionId=$(./tools/getsetting.py subscription_id)
storageConnectionString=$(./tools/getsetting.py account_connstr)

# Disable cloud function that starts container converters (avoid doubles), set app config ConverterDisabled=true
echo "Disabling cloud converters..."
az functionapp config appsettings set -n $rgn -g $rgn --settings ConverterDisabled=true > /dev/null

# Update function config from configuration file
echo "Updating local function settings from configuration.toml"
sed -e "s#STORCONN#$storageConnectionString#g" -e "s#INAME#$rgn#g" -e "s#SKEY#$storageKey#g" -e "s#CID#$clientId#g" -e "s#CSEC#$clientSecret#g" -e "s#TENID#$tenantId#g" -e "s#SUBID#$subscriptionId#g" ./api/local.settings.template > ./api/local.settings.json

# Set API endpoint to localhost for static website
echo "Updating local web frontend to use local functions"
sed -e "s#APIURL#http://localhost:7071#g" ./frontend/js/client-library.template > ./frontend/js/client-library.js

if [ "$1" == "--start" ]
then
    # Start converter
    cd ./converter
    python converter.py &

    # Start functions
    cd ../api
    func host start -p 7071 &

    # Start live-server on port 5500
    cd ../frontend
    live-server --port 5500 . &
fi