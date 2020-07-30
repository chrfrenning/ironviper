#!/usr/bin/env python2.7
import toml
import uuid
import sys
import os
import time
import datetime
import hashlib
import argparse

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


def upload_file(file_name, keep_path, custom_path):
    # find path of the configuraiton file

    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"

    configuration = toml.load(configuration_file_name)
    account_name = configuration["instance_name"]
    account_key = configuration["storage_key"]

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

    destination_path = "/"

    if custom_path is not None and len(custom_path) > 0:
        if custom_path[0] != '/':
            custom_path = "/" + custom_path

        destination_path = custom_path
    
    if keep_path == True:
        relative_path = head.replace("\\", "/") # replace: windows notation change
        if len(relative_path) > 0:
            if relative_path[0] == '.': # remove ./ prefix
                relative_path = relative_path[2:]
            elif relative_path[0] == '/':
                relative_path = relative_path[1:]
                
            destination_path = os.path.join(destination_path, relative_path + '/')

    print "Destination path: " + destination_path


    # Create checksums

    md5, sha256 = create_file_checksums(filename)



    # Create a new unique id for the new blob to make sure we can store it
    # Keep extension from original filename

    destination_filename = uuid.uuid4().hex + filename[filename.rfind('.'):]



    print "Uploading ", filename, " as ", destination_filename
    os.system("az storage blob upload -f '{}' -c file-store -n '{}{}' --account-name {} --account-key {} --metadata 'ORIGINAL_FILENAME={}' 'ORIGINAL_FILETIME={}' 'SOURCE_MD5={}' 'SOURCE_SHA256={}'".format(filename, destination_path[1:], destination_filename, account_name, account_key, original_file_name, original_file_time, md5, sha256))


parser = argparse.ArgumentParser(description='Upload a file to ironviper (azure blob storage)')
parser.add_argument('filename', help="The filename of the file you want to upload.")
parser.add_argument('-k', '--keeppath', default=False, action="store_true", help="Keep path of uploaded file in blob storage, relative to --path")
parser.add_argument('-p', '--path', default=None, help="Specify a destination path/subfolder")

args = parser.parse_args()
upload_file(args.filename, args.keeppath, args.path)