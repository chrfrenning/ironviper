#!/bin/bash

# Setup script for converter image
# Necessary plumbing to run the converter with azure queues and imagemagick

pip install azure-storage-queue   #==2.1.0
pip install azure-storage-blob
pip install azure-keyvault-secrets
pip install azure.identity
pip install azure-cosmosdb-table
pip install shortuuid