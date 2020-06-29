#!/bin/bash

# Setup script for ironviper cloud infrastructure
#
# Author Christopher Frenning christopher@frenning.com; @chrfrenning
# Open Source github.com/chrfrenning/ironviper - see repo for license
#
# Notes: This is an early version and has [many|some|unknown] issues
#
# TODO: Parameterize resource group name and location of services
# TODO: Split resource group name and resource name vars into two separate vars
# Note: Adding random part to resource and rg names to hope for global uniqueness

# Create random number for resource creation
# Keeping this at the beginning of the script to make basic customization easy
rnd=$(cut -c1-6 /proc/sys/kernel/random/uuid)
rgn=ironviper00$rnd
location=centralus

# TODO: Ensure we have tools we need, e.g. jq and python
# sudo apt install jq # note, script intended for azure shell, has jq and python

# Ensure we have the right resource providers
# We may need a mechanism to wait for them all to complete before proceeding
# az provider register --namespace Microsoft.Storage
# az provider register --namespace Microsoft.Web
# az provider register --namespace Microsoft.DocumentDB # dont need yet
# az provider register --namespace Microsoft.CognitiveServices # dont need yet

# Get the code, clone git repo https://github.com/chrfrenning/ironviper.git
git clone https://github.com/chrfrenning/ironviper.git $rgn
cd $rgn

# Time to get going and do some real stuff!
echo Deploying ironviper resources
az group create --location $location --name $rgn

# Save resource group name for app
echo "instance_name = \"$rgn\"" > ./configuration.toml
echo "resource_group = \"$rgn\"" >> ./configuration.toml

# Create keyvault for secrets
az keyvault create -n $rgn -g $rgn --location $location

# Create service principal
az ad sp create-for-rbac -n "http://$rgn" --sdk-auth > ./serviceprincipal.json

clientId=$(cat ./serviceprincipal.json | jq -r ".clientId")
echo "client_id = \"$clientId\"" >> ./configuration.toml

clientSecret=$(cat ./serviceprincipal.json | jq -r ".clientSecret")
echo "client_secret = \"$clientSecret\"" >> ./configuration.toml

tenantId=$(cat ./serviceprincipal.json | jq -r ".tenantId")
echo "tenant_id = \"$tenantId\"" >> ./configuration.toml

az keyvault set-policy -n $rgn --spn $clientId --secret-permissions get list --key-permissions encrypt decrypt get list

# Create storage account
# This is used to host a static website with the altizator.js script
az storage account create -n $rgn -g $rgn --sku "Standard_LRS" --location $location --kind "StorageV2" --access-tier "Hot"

storageKey=$(az storage account keys list -n $rgn -g $rgn --query "[?keyName=='key1'].value" -o tsv)
az keyvault secret set --vault-name $rgn --name "storageKey" --value "$storageKey"
echo "account_key = \"$storageKey\"" >> ./configuration.toml

az storage container create --account-name $rgn --name "file-store" --account-key $storageKey
az storage container create --account-name $rgn --name "pv-store" --account-key $storageKey
az storage queue create --account-name $rgn --name "extract-queue" --account-key $storageKey
az storage table create --account-name $rgn --name "files" --account-key $storageKey
az storage table create --account-name $rgn --name "orphans" --account-key $storageKey

# Hook up storage events to the extract-queue
storageId=$(az storage account show -n $rgn -g $rgn --query id --output tsv)
queueId=$storageId/queueservices/default/queues/extract-queue
subjectFilter="/blobServices/default/containers/file-store/blobs/"
az eventgrid event-subscription create --name "new-files-to-extractors" --source-resource-id $storageId --subject-begins-with $subjectFilter --endpoint-type "storagequeue" --endpoint $queueId

# TODO: Build and push static webfrontend to $web in storage account

az storage blob service-properties update --account-name $rgn --account-key $storageKey --static-website --404-document 404.html --index-document index.html
az storage blob upload-batch -s ./frontend -d '$web' --account-name $rgn --account-key $storageKey
staticurl=$(az storage account show -n $rgn -g $rgn --query "primaryEndpoints.web" --output tsv)
echo "static_url = \"$staticurl\"" >> ./configuration.toml

# TODO: Set up functions on consumption plan and push api
az storage account create -n fn$rnd -l $location -g $rgn --sku Standard_LRS --kind "StorageV2" # not sure if we need a separate storage account?
az resource create -g $rgn -n $rgn --resource-type "Microsoft.Insights/components" --properties {\"Application_Type\":\"web\"}

# TODO: Revisit at a later stage, see https://github.com/Azure/azure-cli/issues/11195
# az functionapp plan create -n $rgn -g $rgn --sku Dynamic
# above doesn't work. no way to create a consumption plan explicitly, this means we have to live with the plan being named by the system

az functionapp create -n $rgn -g $rgn --storage-account fn$rnd --consumption-plan-location $location --app-insights $rgn --runtime node --functions-version 3
functionsurl=$(az functionapp list -g $rgn | jq -r ".[].hostNames[0]")
echo "functions_url = \"$staticurl\"" >> ./configuration.toml

# Create ./api/local.settings.json file with correct cfg parameters
sed -e "s#INAME#$rgn#g" -e "s#SKEY#$storageKey#g" ./api/local.settings.template | tee ./api/local.settings.json

# Push $staticurl onto ./api/proxies.json to refer to correct backend

sed -e "s#BACKEND#$staticurl#g" ./api/proxies.template | tee ./api/proxies.json

# TODO: Update ./api/local.settings.json with InstanceName and StorageAccountKey for local debugging

mkdir tmp
cd api
zip -r ../tmp/api.zip *
cd ..
az functionapp deployment source config-zip -g $rgn -n $rgn --src ./tmp/api.zip

az functionapp config appsettings set --n $rgn -g $rgn --settings "InstanceName=$rgn;StorageAccountKey=$storageKey"
# TODO: Make function app get storage key from keyvault instead of configuration

# TODO: Setup ACI for converter container image

az acr create -g $rgn --name $rgn --sku Basic
az acr login --name $rgn
registryUrl=$(az acr show --n $rgn -g $rgn --query "loginServer" --output tsv)
echo "registry_url = \"$registryUrl\"" >> ./configuration.toml

docker tag ironviper-converter $registryUrl/ironviper-converter:latest

# Build and push docker image
docker build -t ironviper-converter ./converter/.
docker push $registryUrl/ironviper-converter:latest

# TODO: Set up cdn? #notyet #keepcostsatminimum #easytodoyourself

# Download some test files and send them to the system for ingestion
azcopy copy https://chphno.blob.core.windows.net/ironviper-testfiles/ ./tmp --recursive # standard sample file collection
for f in ./tmp/ironviper-testfiles/*; do python ./tools/upload.py $f; done # push all files into the system

# #####################################################################
# 
# Optionally setup development environment on local instance
#

if [ "$1" = "--development" ]; then

    echo "--development set, prepping this environ for development on ironviper"
    echo "note this will store sensitive info on your computer, keep it safe (configuration.toml, ) keys safe"
    
    pip install -r ./converter/requirements.txt

    sudo docker build -t ironviper-converter ./converter/.

    # using embedded in docker pyhon image for now (no digcam support)
    # curl https://imagemagick.org/download/binaries/magick > ./converter/magick
    # chmod +x ./converter/magick
    # sudo apt-get install ufraw-batch # install ufraw
    # that didn't work in docker, have to build imagemagick, thats for later

    # TODO: Build dcraw, ufraw-batch, exiftool, imagemagick
    # TODO: Write from configuration to /frontend/local.settings.json for easier debugging, we need instancename and storagekey
else
    rm -rf ./$rgn
fi


echo "Done. See new resource group in azure: $rgn"
echo "(Not quite there yet, but some stuff working, investigate and have fun - or try again in a few cycles...)"