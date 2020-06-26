#!/bin/bash

# Setup script for ironviper
# TODO: Clone Git Repository and do actual work

echo "Not quite there yet, try again in a few cycles..."

sudo docker build -t ironviper-converter ./converter/.

sudo chmod +x ./infrastructure/deploy_azure.sh
./infrastructure/deploy_azure.sh


# #####################################################################
# 
# Optionally setup development environment on local instance
#

pip install --no-cache-dir -r requirements.txt

# install imagemagick
# that didn't work in docker, have to build imagemagick, thats for later
# using embedded in docker pyhon image for now (no digcam support)
# curl https://imagemagick.org/download/binaries/magick > ./converter/magick
# chmod +x ./converter/magick
# sudo apt-get install ufraw-batch # install ufraw

# TODO: Write from configuration to /frontend/local.settings.json for easier debugging, we need instancename and storagekey

echo "Done. See new resource group: $rng"