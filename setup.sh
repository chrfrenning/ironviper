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

Y='\033[1;33m'
R='\033[0;31m'
G='\033[0;32m'
NC='\033[0m' # No Color



# Startup information

echo -e "${Y}Starting setup at $(date)${NC}.\nSee setup.log for verbose log info."
echo -e "${G}Version: 2020-07-27-4"



# Check script parameters (--noclone and --development)

noclone=0
devmode=0

while test $# -gt 0
do
    case "$1" in
        --noclone) 
            echo "--noclone parameter set"
            noclone=1
            ;;
        --development) 
            echo "--development mode parameter set"
            devmode=1
            ;;
        --*) 
            echo "bad option $1"
            exit 1
            ;;
        *) 
            echo "bad argument $1"
            exit 1
            ;;
    esac
    shift
done



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

if [ $noclone -eq 0 ]
then
    echo -e "${Y}Cloning code from GitHub...${NC}"
    git clone https://github.com/chrfrenning/ironviper.git $rgn || echo -e "${R}Failed.${NC}"
    cd $rgn
else
    echo -e "${Y}Not cloning from GitHub, using current folder+branch...${NC}"
fi



# Time to get going and do some real stuff!

echo "Starting setup at $(date)." > setup.log

echo -e "${Y}Creating resource group...${NC}"
az group create --location $location --name $rgn >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

# Save resource group name for app
echo "instance_name = \"$rgn\"" > ./configuration.toml
echo "resource_group = \"$rgn\"" >> ./configuration.toml

subscriptionId=$(az account show | jq -r ".id")
echo "subscription_id = \"$subscriptionId\"" >> ./configuration.toml



# Create keyvault for secrets

echo -e "${Y}Creating vault for secrets...${NC}"
az keyvault create -n $rgn -g $rgn --location $location >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Create service principal

echo -e "${Y}Creating service principal to access vault...${NC}"
az ad sp create-for-rbac -n "http://$rgn" --sdk-auth > ./serviceprincipal.json

clientId=$(cat ./serviceprincipal.json | jq -r ".clientId")
az keyvault secret set --vault-name $rgn --name "client-id" --value "$clientId"
echo "client_id = \"$clientId\"" >> ./configuration.toml

clientSecret=$(cat ./serviceprincipal.json | jq -r ".clientSecret")
az keyvault secret set --vault-name $rgn --name "client-secret" --value "$clientSecret"
echo "client_secret = \"$clientSecret\"" >> ./configuration.toml

tenantId=$(cat ./serviceprincipal.json | jq -r ".tenantId")
az keyvault secret set --vault-name $rgn --name "tenant-id" --value "$tenantId"
echo "tenant_id = \"$tenantId\"" >> ./configuration.toml


# Give access to service principal to read from key vault

echo -e "${Y}Granting access to read from vault...${NC}"
az keyvault set-policy -n $rgn --spn $clientId --secret-permissions get list --key-permissions encrypt decrypt get list >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"


# Give access to service principal to resource group

echo -e "${Y}Granting access to control resources...${NC}"
spObjectId=$(az ad sp list --display-name $rgn --query [].objectId --output tsv)
az role assignment create --role Contributor --assignee-object-id $spObjectId --assignee-principal-type ServicePrincipal --resource-group $rgn >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Create cognitive services

echo -e "${Y}Creating cognitive services instance...${NC}"
az cognitiveservices account create --name $rgn --resource-group $rgn --kind CognitiveServices --sku S0 --location $location >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

cognitiveServicesKey=$(az cognitiveservices account keys list -n $rgn -g $rgn --query "key1" -o tsv)
az keyvault secret set --vault-name $rgn --name "cognitive-key" --value "$cognitiveServicesKey" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "cognitive_key = \"$storageKey\"" >> ./configuration.toml

cognitiveEndpoint=$(az cognitiveservices account show -n $rgn -g $rgn --query "properties.endpoint" --output tsv)
az keyvault secret set --vault-name $rgn --name "cognitive-endpoint" --value "$cognitiveEndpoint" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "cognitive_endpoint = \"$cognitiveEndpoint\"" >> ./configuration.toml



# Create storage account
# This is used to store files, previews, our static website, functions sync files, etc

echo -e "${Y}Creating storage...${NC}"
az storage account create -n $rgn -g $rgn --sku "Standard_LRS" --location $location --kind "StorageV2" --access-tier "Hot" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

storageKey=$(az storage account keys list -n $rgn -g $rgn --query "[?keyName=='key1'].value" -o tsv)
az keyvault secret set --vault-name $rgn --name "storage-key" --value "$storageKey" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "storage_key = \"$storageKey\"" >> ./configuration.toml

storageConnectionString=$(az storage account show-connection-string -n $rgn --query "connectionString" --output tsv)
az keyvault secret set --vault-name $rgn --name "storage-connstr" --value "$storageConnectionString" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "storage_connstr = \"$storageConnectionString\"" >> ./configuration.toml

az storage container create --account-name $rgn --name "file-store" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage container create --account-name $rgn --name "pv-store" --public-access blob --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage queue create --account-name $rgn --name "extract-queue" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage table create --account-name $rgn --name "files" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage table create --account-name $rgn --name "folders" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage table create --account-name $rgn --name "orphans" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Create event grid

echo -e "${Y}Creating event grid...${NC}"

az eventgrid topic create -n $rgn -g $rgn -l $location >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

eventGridKey=$(az eventgrid topic key list -n $rgn -g $rgn --query "key1" -o tsv)
az keyvault secret set --vault-name $rgn --name "eventgrid-key" --value "$eventGridKey" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "eventgrid_key = \"$eventGridKey\"" >> ./configuration.toml

eventGridEndpoint=$(az eventgrid topic show -n $rgn -g $rgn --query "endpoint" --output tsv)
az keyvault secret set --vault-name $rgn --name "eventgrid-endpoint" --value "$eventGridEndpoint" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "eventgrid_endpoint = \"$eventGridEndpoint\"" >> ./configuration.toml


# Hook up storage events to the extract-queue

echo -e "${Y}Hooking up file detection events...${NC}"

storageId=$(az storage account show -n $rgn -g $rgn --query id --output tsv)
queueId=$storageId/queueservices/default/queues/extract-queue
subjectFilter="/blobServices/default/containers/file-store/blobs/"
az eventgrid event-subscription create --name "new-files-to-extractors" --source-resource-id $storageId --subject-begins-with $subjectFilter --endpoint-type "storagequeue" --endpoint $queueId >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Set up functions on consumption plan and push api

echo -e "${Y}Creating functionapp for serverless API...${NC}"

az resource create -g $rgn -n $rgn --resource-type "Microsoft.Insights/components" --properties {\"Application_Type\":\"web\"} >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

# TODO: Revisit at a later stage, see https://github.com/Azure/azure-cli/issues/11195
# az functionapp plan create -n $rgn -g $rgn --sku Dynamic
# above doesn't work. no way to create a consumption plan explicitly, this means we have to live with the plan being named by the system

az functionapp create -n $rgn -g $rgn --storage-account $rgn --consumption-plan-location $location --app-insights $rgn --runtime node --functions-version 3 >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
functionsurl=$(az functionapp list -g $rgn | jq -r ".[].hostNames[0]")
echo "functions_url = \"$functionsurl\"" >> ./configuration.toml

# Create ./api/local.settings.json file with correct cfg parameters
sed -e "s#STORCONN#$storageConnectionString#g" -e "s#INAME#$rgn#g" -e "s#SKEY#$storageKey#g" -e "s#CID#$clientId#g" -e "s#CSEC#$clientSecret#g" -e "s#TENID#$tenantId#g" -e "s#SUBID#$subscriptionId#g" ./api/local.settings.template > ./api/local.settings.json



# Push api code to server

cd api

echo -e "${Y}Retrieving dependencies...${NC}"
npm install >> ../setup.log 2>&1 || echo -e "${R}Failed.${NC}"


echo -e "${Y}Package api code...${NC}"

mkdir ../tmp
zip -r ../tmp/api.zip * >> ../setup.log 2>&1 || echo -e "${R}Failed.${NC}"
cd ..


echo -e "${Y}Deploying api code...${NC}"

az functionapp deployment source config-zip -g $rgn -n $rgn --src ./tmp/api.zip >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

# Push settings to azure functions
# TODO: Make function app get storage key from keyvault instead of configuration

echo -e "${Y}Pushing settings to function app...${NC}"
az functionapp config appsettings set -n $rgn -g $rgn --settings InstanceName=$rgn StorageAccountKey=$storageKey ClientId=$clientId ClientSecret=$clientSecret TenantId=$tenantId SubscriptionId=$subscriptionId >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Build and push static webfrontend to $web in storage account

echo -e "${Y}Creating static website and pushing code...${NC}"

az storage blob service-properties update --account-name $rgn --account-key $storageKey --static-website --404-document index.html --index-document index.html >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

sed -e "s#APIURL#https://$functionsurl#g" ./frontend/js/client-library.template > ./frontend/js/client-library.js
az storage blob upload-batch -s ./frontend -d '$web' --account-name $rgn --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

staticurl=$(az storage account show -n $rgn -g $rgn --query "primaryEndpoints.web" --output tsv)
echo "static_url = \"$staticurl\"" >> ./configuration.toml


# Change CORS to allow static website to access

az functionapp cors add -n $rgn -g $rgn --allowed-origins ${staticurl:0:-1}
if [ $devmode -eq 1 ]
then
  az functionapp cors add -n $rgn -g $rgn --allowed-origins http://localhost:5500/
fi



# Setup ACI for converter container image

echo -e "${Y}Creating container registry for background tasks...${NC}"

az acr create -g $rgn --name $rgn --sku Basic # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
#az acr login --name $rgn # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
registryUrl=$(az acr show --n $rgn -g $rgn --query "loginServer" --output tsv)
az keyvault secret set --vault-name $rgn --name "registry-url" --value "$registryUrl" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "registry_url = \"$registryUrl\"" >> ./configuration.toml

# Get registry credentials

az acr update -n $rgn --admin-enabled # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
registryUsername=$(az acr credential show -n $rgn --query username --output tsv)
registryPassword=$(az acr credential show -n $rgn --query passwords[?name==\'password\'].value --output tsv)

az keyvault secret set --vault-name $rgn --name "registry-username" --value "$registryUsername" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az keyvault secret set --vault-name $rgn --name "registry-password" --value "$registryPassword" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

echo "registry_username = \"$registryUsername\"" >> ./configuration.toml
echo "registry_password = \"$registryPassword\"" >> ./configuration.toml



# Build and push docker image

echo -e "${Y}Building and pushing converter container image...${NC}"
az acr build --registry $rgn --image ironviper-converter:latest ./converter/ # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Spin up the primary converter container
# TODO: Switching to docker hub image instead of azure container registry to get rid of $5/month cost, need
#       automated pipeline on main branch to keep docker hub up-to-date and a bit more structured PR approach to
#       avoid breakign running systems.

echo -e "${Y}Starting container instances...${NC}"
memory=1 # configure this to optimize available memory for containers. leaving at 1 while in poc mode, increase to 3 for large files
# TODO: Adjust memory for conversion containers

az container create -g $rgn -n $rgn-converter-09 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-08 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-07 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-06 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-05 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-04 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-03 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-02 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-01 --no-wait --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-00 --cpu 1 --memory $memory --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# TODO: Set up cdn? #notyet #keepcostsatminimum #easytodoyourself



# #####################################################################
# 
# We're done, info on how to use
#

echo -e "${G}Done.${NC}"
echo -e "${NC}Created resource group ${rgn} in azure.${NC}"
echo -e "${G}Browse website: ${staticurl} to test the system.${NC}"
echo -e "${NC}(Api at https://${functionsurl}/api/)${NC}"
echo -e "${NC}(Note: We're not quite finished yet - not even a PoC - but some stuff is working, investigate and have fun - or try again in a few cycles...)${NC}"


# Download some test files and send them to the system for ingestion
# standard sample file collection at https://chphno.blob.core.windows.net/ironviper-testfiles/

echo -e "${Y}Downloading test files...${NC}"
mkdir ./tmp/ironviper-testfiles
cd ./tmp/ironviper-testfiles
wget --quiet https://chphno.blob.core.windows.net/ironviper-testfiles/DSCF8510.jpg
wget --quiet https://chphno.blob.core.windows.net/ironviper-testfiles/DSCF8525.jpg
# TODO: Add new file formats as we add support for them
cd ../..

# Ingest test files into the file-store

echo -e "${Y}Uploading test files to check system...${NC}"
az storage blob upload-batch -s ./tmp/ironviper-testfiles -d 'file-store' --account-name $rgn --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# #####################################################################
# 
# Optionally setup development environment on local instance
#


if [ $devmode -eq 1 ]
then

    echo "--development set, prepping this environ for development on ironviper"
    echo "note this will store sensitive info on your computer, keep it safe (configuration.toml, serviceprincipal.json)"
    
    sudo npm install -g live-server
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
    echo -e "${Y}Cleaning up...${NC}"
    # rm -rf ./$rgn
fi

