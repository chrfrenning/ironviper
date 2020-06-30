#!/bin/bash

# Update script for ironviper cloud infrastructure
#
# Author Christopher Frenning christopher@frenning.com; @chrfrenning
# Open Source github.com/chrfrenning/ironviper - see repo for license
#
# This script will push the version of the code found locally to 
# the cloud
#

rgn=$(./tools/getsetting.py instance_name)
storageKey=$(./tools/getsetting.py account_key)
registryUrl=$(./tools/getsetting.py registry_url)
registryUsername=$(./tools/getsetting.py registry_username)
registryPassword=$(./tools/getsetting.py registry_password)
staticurl=$(./tools/getsetting.py static_url)
functionsurl=$(./tools/getsetting.py functions_url)
echo instance: $rgn\nstoragekey: $storageKey\nregistry: $registryUrl\nusr: $registryUsername\npwd: $registryPassword\nstaticurl: $staticurl\nfunctionsurl: $functionsurl\n

# Build and push static webfrontend to $web in storage account
az storage blob upload-batch -s ./frontend -d '$web' --account-name $rgn --account-key $storageKey

# Update functions config and push latest code 

sed -e "s#BACKEND#$staticurl#g" ./api/proxies.template | tee ./api/proxies.json

mkdir tmp
rm ./tmp/api.zip

cd api
zip -r ../tmp/api.zip *
cd ..

az functionapp deployment source config-zip -g $rgn -n $rgn --src ./tmp/api.zip
az functionapp config appsettings set --n $rgn -g $rgn --settings "InstanceName=$rgn;StorageAccountKey=$storageKey"

# Build docker image

docker build -t ironviper-converter ./converter/.
docker tag ironviper-converter $registryUrl/ironviper-converter:latest

# Deploy to container registry

az acr login --name $rgn
az acr update -n $rgn --admin-enabled

docker push $registryUrl/ironviper-converter:latest

# Spin up the primary converter container

az container create -g $rgn -n $rgn-primary-converter --image $registryUrl/ironviper-converter:latest --registry-login-server $registryUrl --registry-username $registryUsername --registry-password $registryPassword -e INSTANCE_NAME=$rgn ACCOUNT_KEY=$storageKey

echo "Done. Browse website: $functionsurl"