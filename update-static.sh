#!/bin/bash

# Update script for ironviper cloud infrastructure
#
# Author Christopher Frenning christopher@frenning.com; @chrfrenning
# Open Source github.com/chrfrenning/ironviper - see repo for license
#
# This script will push the version of the code found locally to 
# the cloud
#

# Get settings

rgn=$(./tools/getsetting.py instance_name)
storageKey=$(./tools/getsetting.py storage_key)
registryUrl=$(./tools/getsetting.py registry_url)
registryUsername=$(./tools/getsetting.py registry_username)
registryPassword=$(./tools/getsetting.py registry_password)
staticurl=$(./tools/getsetting.py static_url)
functionsurl=$(./tools/getsetting.py functions_url)
clientId=$(./tools/getsetting.py client_id)
clientSecret=$(./tools/getsetting.py client_secret)
tenantId=$(./tools/getsetting.py tenant_id)
subscriptionId=$(./tools/getsetting.py subscription_id)

# Build and push static webfrontend to $web in storage account

echo -e "${Y}Uploading static website...${NC}"

sed -e "s#APIURL#https://$functionsurl#g" ./frontend/js/client-library.template > ./frontend/js/client-library.js
az storage blob upload-batch -s ./frontend -d '$web' --account-name $rgn --account-key $storageKey