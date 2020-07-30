#!/bin/bash

# Update script for ironviper cloud infrastructure
#
# Author Christopher Frenning christopher@frenning.com; @chrfrenning
# Open Source github.com/chrfrenning/ironviper - see repo for license
#
# This script will push the version of the code found locally to 
# the cloud
#

Y='\033[1;33m'
R='\033[0;31m'
G='\033[0;32m'
NC='\033[0m' # No Color



# Create log file

echo -e "${G}Starting upgrade at $(date)${NC}.\nSee update.log for verbose log info."
echo "Starting upgrade at $(date)." > update.log



# Get settings

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

echo -e "instance: $rgn\nstoragekey: $storageKey\nregistry: $registryUrl\nusr: $registryUsername\npwd: $registryPassword\nstaticurl: $staticurl\nfunctionsurl: $functionsurl\n" >> update.log



# Build and push static webfrontend to $web in storage account

echo -e "${Y}Uploading static website...${NC}"

sed -e "s#APIURL#https://$functionsurl#g" ./frontend/js/client-library.template > ./frontend/js/client-library.js
az storage blob upload-batch -s ./frontend -d '$web' --account-name $rgn --account-key $storageKey >> update.log 2>&1 || echo -e "${R}Failed.${NC}"



# Update functions config and push latest code 

echo -e "${Y}Uploading azure functions code...${NC}"

mkdir tmp >> update.log  2>&1
rm ./tmp/api.zip >> update.log 2>&1

cd api
zip -r ../tmp/api.zip * >> ../update.log 2>&1  || echo -e "${R}Failed.${NC}"
cd ..

az functionapp deployment source config-zip -g $rgn -n $rgn --src ./tmp/api.zip >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az functionapp config appsettings set --n $rgn -g $rgn --settings InstanceName=$rgn StorageAccountKey=$storageKey ClientId=$clientId ClientSecret=$clientSecret TenantId=$tenantId SubscriptionId=$subscriptionId >> update.log 2>&1 || echo -e "${R}Failed.${NC}"



# Build docker image

echo -e "${Y}Building docker image...${NC}"
docker build -t ironviper-converter ./converter/. >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
docker tag ironviper-converter $registryUrl/ironviper-converter:latest >> update.log 2>&1 || echo -e "${R}Failed.${NC}"



# Deploy to container registry

echo -e "${Y}Deploying docker image...${NC}"
az acr login --name $rgn >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az acr update -n $rgn --admin-enabled >> update.log 2>&1 || echo -e "${R}Failed.${NC}"

docker push $registryUrl/ironviper-converter:latest >> update.log 2>&1 || echo -e "${R}Failed.${NC}"



# Spin up the primary converter container

echo -e "${Y}Starting container instances...${NC}"

az container create -g $rgn -n $rgn-converter-09 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-08 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-07 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-06 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-05 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-04 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-03 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-02 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-01 --no-wait --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"
az container create -g $rgn -n $rgn-converter-00 --cpu 1 --memory 3 --restart-policy OnFailure --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey  >> update.log 2>&1 || echo -e "${R}Failed.${NC}"


# We're done

echo -e "${G}Done. Browse website: $functionsurl ${NC}"
