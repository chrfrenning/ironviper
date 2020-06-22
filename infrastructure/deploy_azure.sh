#!/bin/bash

# Setup script for ironviper cloud infrastructure
#
# Author Christopher Frenning chfrenni@microsoft.com @chrfrenning
# Open Source github.com/chrfrenning/ironviper - see repo for license
#
# Notes: This is an early version and has [many|some|unknown] issues
#
# TODO: Parameterize resource group name and location of services
# TODO: Split resource group name and resource name vars into two separate vars
# NOTE: Adding random part to resource and rg names to hope for global uniqueness

# Create random number for resource creation
# TODO: More parameterization of the setup should happen here, which resources to create?
# Keeping this at the beginning of the script to make basic customization easy
rnd=$(cut -c1-6 /proc/sys/kernel/random/uuid)
rgn=ironviper00$rnd
location=centralus

# TODO: Ensure we have tools we need, e.g. jq
# sudo apt install jq

# Ensure we have the right resource providers
# We may need a mechanism to wait for them all to complete before proceeding
# az provider register --namespace Microsoft.DocumentDB
# az provider register --namespace Microsoft.CognitiveServices
# az provider register --namespace Microsoft.Web
# az provider register --namespace Microsoft.Storage

# Time to get going and do some real stuff!
echo Deploying ironviper resources
az group create --location $location --name $rgn

# Save resource group name for app
echo "instance_name = \"$rgn\"" > ../configuration.toml
echo "resource_group = \"$rgn\"" >> ../configuration.toml

# Create keyvault for secrets
az keyvault create -n $rgn -g $rgn --location $location

# Create service principal
az ad sp create-for-rbac -n "http://$rgn" --sdk-auth > ../serviceprincipal.json
clientId = $(cat serviceprincipal.json | jq -r ".clientId")
echo "client_id = \"$clientId\"" >> ../configuration.toml

clientSecret = $(cat serviceprincipal.json | jq -r ".clientSecret")
echo "client_secret = \"$clientSecret\"" >> ../configuration.toml

tenantId = $(cat serviceprincipal.json | jq -r ".tenantId")
echo "tenant_id = \"$clientSecret\"" >> ../configuration.toml

az keyvault set-policy -n @rgn --spn $clientId --secret-permissions get list --key-permissions encrypt decrypt get list

# Create storage account
# This is used to host a static website with the altizator.js script
az storage account create -n $rgn -g $rgn --sku "Standard_LRS" --location $location --kind "StorageV2" --access-tier "Hot"

storageKey=$(az storage account keys list -n $rgn -g $rgn --query "[?keyName=='key1'].value" -o tsv)
az keyvault secret set --vault-name $rgn --name "storageKey" --value "$storageKey"
echo "account_key = \"$storageKey\"" >> ../configuration.toml

az storage container create --account-name $rgn --name "file-store"
az storage container create --account-name $rgn --name "pv-store"
az storage queue create --account-name $rgn --name "extract-queue"
az storage table create --account-name $rgn --name "files"

# Hook up storage events to the extract-queue
storageId=$(az storage account show -n $rgn -g $rgn --query id --output tsv)
queueId=$storageId/queueservices/default/queues/extract-queue
# TODO: Update subject-begins-with to only include events from the file-store container
subjectFilter="/blobServices/default/containers/file-store/blobs/"
az eventgrid event-subscription create --name "new-files-to-extractors" --source-resource-id $storageId --subject-begins-with $subjectFilter --endpoint-type "storagequeue" --endpoint $queueId


