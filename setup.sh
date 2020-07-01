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



# Create random number for resource creation
# Keeping this at the beginning of the script to make basic customization easy

rnd=$(cut -c1-6 /proc/sys/kernel/random/uuid)
rgn=ironviper00$rnd
location=centralus



# Create log file

echo -e "${Y}Starting setup at $(date)${NC}.\nSee setup.log for verbose log info."
echo -e "${G}Version: 2020-06-30-4"



# TODO: Ensure we have tools we need, e.g. jq and python
# sudo apt install jq # note, script intended for azure shell, has jq and python

# Ensure we have the right resource providers
# We may need a mechanism to wait for them all to complete before proceeding
# az provider register --namespace Microsoft.Storage
# az provider register --namespace Microsoft.Web
# az provider register --namespace Microsoft.DocumentDB # dont need yet
# az provider register --namespace Microsoft.CognitiveServices # dont need yet



# Get the code, clone git repo https://github.com/chrfrenning/ironviper.git

echo -e "${Y}Cloning code from GitHub...${NC}"
git clone https://github.com/chrfrenning/ironviper.git $rgn || echo -e "${R}Failed.${NC}"
cd $rgn



# Time to get going and do some real stuff!

echo "Starting setup at $(date)." > setup.log

echo -e "${Y}Creating resource group...${NC}"
az group create --location $location --name $rgn >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

# Save resource group name for app
echo "instance_name = \"$rgn\"" > ./configuration.toml
echo "resource_group = \"$rgn\"" >> ./configuration.toml



# Create keyvault for secrets

echo -e "${Y}Creating vault for secrets...${NC}"
az keyvault create -n $rgn -g $rgn --location $location >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Create service principal

echo -e "${Y}Creating service principal to access vault...${NC}"
az ad sp create-for-rbac -n "http://$rgn" --sdk-auth > ./serviceprincipal.json

clientId=$(cat ./serviceprincipal.json | jq -r ".clientId")
echo "client_id = \"$clientId\"" >> ./configuration.toml

clientSecret=$(cat ./serviceprincipal.json | jq -r ".clientSecret")
echo "client_secret = \"$clientSecret\"" >> ./configuration.toml

tenantId=$(cat ./serviceprincipal.json | jq -r ".tenantId")
echo "tenant_id = \"$tenantId\"" >> ./configuration.toml

az keyvault set-policy -n $rgn --spn $clientId --secret-permissions get list --key-permissions encrypt decrypt get list >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Create storage account
# This is used to host a static website with the altizator.js script

echo -e "${Y}Creating storage...${NC}"
az storage account create -n $rgn -g $rgn --sku "Standard_LRS" --location $location --kind "StorageV2" --access-tier "Hot" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

storageKey=$(az storage account keys list -n $rgn -g $rgn --query "[?keyName=='key1'].value" -o tsv)
az keyvault secret set --vault-name $rgn --name "storageKey" --value "$storageKey" >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
echo "account_key = \"$storageKey\"" >> ./configuration.toml

az storage container create --account-name $rgn --name "file-store" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage container create --account-name $rgn --name "pv-store" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage queue create --account-name $rgn --name "extract-queue" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage table create --account-name $rgn --name "files" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage table create --account-name $rgn --name "orphans" --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Hook up storage events to the extract-queue

echo -e "${Y}Hooking up file detection events...${NC}"

storageId=$(az storage account show -n $rgn -g $rgn --query id --output tsv)
queueId=$storageId/queueservices/default/queues/extract-queue
subjectFilter="/blobServices/default/containers/file-store/blobs/"
az eventgrid event-subscription create --name "new-files-to-extractors" --source-resource-id $storageId --subject-begins-with $subjectFilter --endpoint-type "storagequeue" --endpoint $queueId >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# Build and push static webfrontend to $web in storage account

echo -e "${Y}Creating static website and pushing code...${NC}"

az storage blob service-properties update --account-name $rgn --account-key $storageKey --static-website --404-document 404.html --index-document index.html >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az storage blob upload-batch -s ./frontend -d '$web' --account-name $rgn --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
staticurl=$(az storage account show -n $rgn -g $rgn --query "primaryEndpoints.web" --output tsv)
echo "static_url = \"$staticurl\"" >> ./configuration.toml



# Set up functions on consumption plan and push api

echo -e "${Y}Creating functionapp for serverless API...${NC}"

az storage account create -n fn$rnd -l $location -g $rgn --sku Standard_LRS --kind "StorageV2"  >> setup.log 2>&1 || echo -e "${R}Failed.${NC}" # not sure if we need a separate storage account?
az resource create -g $rgn -n $rgn --resource-type "Microsoft.Insights/components" --properties {\"Application_Type\":\"web\"} >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"

# TODO: Revisit at a later stage, see https://github.com/Azure/azure-cli/issues/11195
# az functionapp plan create -n $rgn -g $rgn --sku Dynamic
# above doesn't work. no way to create a consumption plan explicitly, this means we have to live with the plan being named by the system

az functionapp create -n $rgn -g $rgn --storage-account fn$rnd --consumption-plan-location $location --app-insights $rgn --runtime node --functions-version 3 >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
functionsurl=$(az functionapp list -g $rgn | jq -r ".[].hostNames[0]")
echo "functions_url = \"$staticurl\"" >> ./configuration.toml

# Create ./api/local.settings.json file with correct cfg parameters
sed -e "s#INAME#$rgn#g" -e "s#SKEY#$storageKey#g" ./api/local.settings.template > ./api/local.settings.json

# Push $staticurl onto ./api/proxies.json to refer to correct backend

sed -e "s#BACKEND#$staticurl#g" ./api/proxies.template > ./api/proxies.json



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
az functionapp config appsettings set --n $rgn -g $rgn --settings InstanceName=$rgn StorageAccountKey=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"




# Setup ACI for converter container image

echo -e "${Y}Creating container registry for background tasks...${NC}"

az acr create -g $rgn --name $rgn --sku Basic # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
#az acr login --name $rgn # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
registryUrl=$(az acr show --n $rgn -g $rgn --query "loginServer" --output tsv)
echo "registry_url = \"$registryUrl\"" >> ./configuration.toml

# Get registry credentials

az acr update -n $rgn --admin-enabled # >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
registryUsername=$(az acr credential show -n $rgn --query username --output tsv)
registryPassword=$(az acr credential show -n $rgn --query passwords[?name==\'password\'].value --output tsv)

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

az container create -g $rgn -n $rgn-converter-09 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-08 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-07 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-06 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-05 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-04 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-03 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-02 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-01 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-00 --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# TODO: Set up cdn? #notyet #keepcostsatminimum #easytodoyourself



# Download some test files and send them to the system for ingestion

echo -e "${Y}Downloading test files...${NC}"
azcopy copy https://chphno.blob.core.windows.net/ironviper-testfiles/ ./tmp --recursive # standard sample file collection

# Ingest test files into the file-store

echo -e "${Y}Uploading test files to check system...${NC}"
az storage blob upload-batch -s ./tmp/ironviper-testfiles -d 'file-store' --account-name $rgn --account-key $storageKey >> setup.log 2>&1 || echo -e "${R}Failed.${NC}"



# #####################################################################
# 
# Optionally setup development environment on local instance
#

if [ "$1" -eq "--development" ]; then

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
    # rm -rf ./$rgn
fi


echo -e "${G}Done.\nSee new resource group in azure: $rgn\nBrowse website: $functionsurl${NC}"
echo -e "${NC}(Note: We're not quite finished yet, but some stuff working, investigate and have fun - or try again in a few cycles...)${NC}"
