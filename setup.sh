#!/bin/bash

# Setup script for ironviper
# TODO: Clone Git Repository and do actual work

echo "Not quite there yet, try again in a few cycles..."

sudo chmod +x ./infrastructure/deploy_azure.sh
./infrastructure/deploy_azure.sh


# #####################################################################
# 
# Optionally setup development environment on local instance
#

pip install --no-cache-dir -r requirements.txt

# install imagemagick

curl https://imagemagick.org/download/binaries/magick > ./converter/magick
chmod +x ./converter/magick

# install ufraw
sudo apt-get install ufraw-batch


# TODO: Write from configuration to /frontend/local.settings.json for easier debugging, we need instancename and storagekey

echo "Done. See new resource group: $rng"