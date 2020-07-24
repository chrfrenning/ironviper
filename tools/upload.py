#!/usr/bin/env python2.7
import toml
import uuid
import sys
import os
import time
import datetime
import hashlib

# checksum creation

def create_file_checksums(file_name):
    BUFSIZE = 65536

    start = time.time()

    md5 = hashlib.md5()
    sha256 = hashlib.sha256()

    with open(file_name, 'rb') as f:
        while True:
            data = f.read(BUFSIZE)
            if not data:
                break
            md5.update(data)
            sha256.update(data)

    print "checksums: md5(", md5.hexdigest(), "), sha256(", sha256.hexdigest(), ")"
    print "create_file_checksums completed in {} seconds".format(time.time()-start)
    return md5.hexdigest(), sha256.hexdigest()



# find path of the configuraiton file

configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"

configuration = toml.load(configuration_file_name)
account_name = configuration["instance_name"]
account_key = configuration["account_key"]

# Check the file we are about to upload

if ( len(sys.argv) < 2 ):
    print "Please specify file to upload as argyment, e.g. python upload.py image.jpg"
    exit(1)

filename = sys.argv[1]
print "File to upload: " + filename
if not os.path.exists(filename):
    print "File does not exist, please specify a valid filename."
    exit(1)

head, tail = os.path.split(filename)
print "Source path: " + head
original_file_name = tail
original_file_time = datetime.datetime.utcfromtimestamp(os.path.getmtime(filename)).isoformat()

#print original_file_name, original_file_time

# convert relative path to server form
# TODO: Ensure paths are url safe, replace illegal chars, separators, whitespace

destination_path = head.replace("\\", "/") # windows notation change
if len(destination_path) > 0:
    if destination_path[0] == '.': # remove ./ prefix
        destination_path = destination_path[2:]
    elif destination_path[0] == '/':
        destination_path = destination_path[1:]
        
    destination_path = destination_path + '/'

print "Destination path: " + destination_path


# Create checksums

md5, sha256 = create_file_checksums(filename)



# Create a new unique id for the new blob to make sure we can store it
# Keep extension from original filename

destination_filename = uuid.uuid4().hex + filename[filename.rfind('.'):]



print "Uploading ", filename, " as ", destination_filename
os.system("az storage blob upload -f '{}' -c file-store -n '{}{}' --account-name {} --account-key {} --metadata 'ORIGINAL_FILENAME={}' 'ORIGINAL_FILETIME={}' 'SOURCE_MD5={}' 'SOURCE_SHA256={}'".format(filename, destination_path, destination_filename, account_name, account_key, original_file_name, original_file_time, md5, sha256))
