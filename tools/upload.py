#!/usr/bin/env python2.7
import toml
import uuid
import sys
import os

# find path of the configuraiton file
configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"

configuration = toml.load(configuration_file_name)
account_name = configuration["instance_name"]
account_key = configuration["account_key"]

if ( len(sys.argv) < 2 ):
    print "Please specify file to upload as argyment, e.g. python upload.py image.jpg"
    exit(1)

filename = sys.argv[1]
destination_filename = uuid.uuid4().hex + filename[filename.rfind('.'):]

print "Uploading ", filename, " as ", destination_filename
os.system("az storage blob upload -f '{}' -c file-store -n '{}' --account-name {} --account-key {}".format(filename, destination_filename, account_name, account_key))
