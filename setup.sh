#!/bin/bash

# Setup script for ironviper
# TODO: Clone Git Repository and do actual work

echo "Not quite there yet, try again in a few cycles..."

sudo chmod +x ./infrastructure/deploy_azure.sh
./infrastructure/deploy_azure.sh

# TODO: Write from configuration to /frontend/local.settings.json for easier debugging, we need instancename and storagekey

echo "Done. See new resource group: $rng"