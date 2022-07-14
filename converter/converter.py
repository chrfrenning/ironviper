#!/usr/bin/env python3

from sqlite3 import Date
import sys
import json
import toml
import os
import uuid
import time
import datetime
import base64
import signal
import random
import subprocess
import hashlib
import shortuuid
from urllib.parse import urlparse
from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient
from azure.storage.blob import ContentSettings
from azure.cosmosdb.table.tableservice import TableService # replace with azure-data-tables? https://docs.microsoft.com/en-us/python/api/overview/azure/data-tables-readme?view=azure-python
from azure.cosmosdb.table.models import Entity
import foldermodel

# Import common code libraries for ironviper, apologies for the path manipulation here
# sys.path.append(os.path.abspath(os.path.dirname(os.path.abspath(__file__))+'/../libs/python'))
from eventgrid import post_event



# #####################################################################
#
# Global variables (hell yeah)

version = "202006300950"
stopSignal = False
debugMode = False
prodMode = False
debugDisableMessageDeque = False

configuration = None



# #####################################################################
#
# Thumbnail creation using imagemagick
#

def create_thumbnails_classic(filename):
    start = time.time()

    os.system("convert {} -resize '1920x1080' -auto-orient -quality 90 -interlace Plane -strip /tmp/hd.jpg".format(filename))
    os.system("convert {} -resize '1600x1600' -auto-orient -quality 80 -interlace Plane -strip /tmp/1600.jpg".format(filename))
    os.system("convert {} -resize '800x800' -auto-orient -quality 80 -interlace Plane -strip /tmp/800.jpg".format(filename))
    os.system("convert {} -resize '600x600' -auto-orient -quality 80 -interlace Plane -strip /tmp/600.jpg".format(filename))
    os.system("convert {} -resize '400x400' -auto-orient -quality 80 -interlace Plane -strip /tmp/400.jpg".format(filename))
    os.system("convert {} -resize 'x400' -auto-orient -quality 80 -interlace Plane -strip /tmp/h400.jpg".format(filename))
    os.system("convert {} -resize '400x' -auto-orient -quality 80 -interlace Plane -strip /tmp/w400.jpg".format(filename))
    os.system("convert {} -resize '200x200' -auto-orient -quality 80 -interlace Plane -strip /tmp/200.jpg".format(filename))
    os.system("convert {} -thumbnail '100x100' -auto-orient /tmp/100.jpg".format(filename))
    os.system("convert {} -thumbnail 100x100^ -gravity center -extent 100x100 -auto-orient /tmp/sq100.jpg".format(filename))

    print("create_thumbnails_classic completed in {} seconds".format(time.time() - start))

    thumbs =  [ "/tmp/sq100.jpg", "/tmp/w400.jpg", "/tmp/h400.jpg", "/tmp/hd.jpg", "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/400.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs
    
    
    
def create_thumbnails_classic_optimized(filename):
    start = time.time()

    os.system("convert {} -resize '1600x>' -quality 80 -interlace Plane -strip /tmp/1600.jpg".format(filename))
    os.system("convert /tmp/1600.jpg -resize '800>' -quality 80 -interlace Plane -strip /tmp/800.jpg".format(filename))
    os.system("convert /tmp/1600.jpg -resize '600>' -quality 80 -interlace Plane -strip /tmp/600.jpg".format(filename))
    os.system("convert /tmp/800.jpg -resize '400>' -quality 80 -interlace Plane -strip /tmp/400.jpg".format(filename))
    os.system("convert /tmp/800.jpg -resize '200>' -quality 80 -interlace Plane -strip /tmp/200.jpg".format(filename))
    os.system("convert /tmp/800.jpg -thumbnail '100x100' /tmp/100.jpg".format(filename))

    print( "create_thumbnails_classic_optimized completed in {} seconds".format(time.time() - start))

    thumbs =  [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs



def create_thumbnails_mpr(filename):
    start = time.time()

    os.system("convert {} -write mpr:main +delete" \
        " mpr:main -resize \"1600x>\" -quality 80 -interlace Plane -strip -write /tmp/1600.jpg +delete" \
        " mpr:main -resize \"800x>\" -quality 80 -interlace Plane -strip -write /tmp/800.jpg +delete" \
        " mpr:main -resize \"600>\" -quality 80 -interlace Plane -strip -write /tmp/600.jpg +delete" \
        " mpr:main -resize \"200x>\" -quality 80 -interlace Plane -strip -write /tmp/200.jpg +delete" \
        " mpr:main -thumbnail \"100x100\" -write /tmp/100.jpg null:".format(filename))
    
    print( "create_thumbnails_mpr completed in {} seconds".format(time.time() - start))
    
    thumbs =  [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs


def create_thumbnails_mpr_optimized(filename):
    start = time.time()
    
    # var = "convert /tmp/b6b262a33e594b99b2375f6b1b96d72d.jpg -resize '1600x>' -quality 80 -interlace Plane 
    # -strip -write mpr:main +delete mpr:main -write ./1600.jpg +delete mpr:main -resize '800x>' 
    # -quality 80 -interlace Plane -strip ./800.jpg"
    
    # convert /tmp/85e22e088eba4bdc889338d2eeee261e.jpg -resize '1600x>' -quality 80 -interlace Plane -strip -write mpr:main +delete 
    # mpr:main -write 1600.jpg +delete 
    # mpr:main -thumbnail '100x100' 100.jpg

    os.system("convert {} -resize '1600x>' -quality 80 -interlace Plane -strip -write mpr:main +delete" \
        " mpr:main -write /tmp/1600.jpg +delete" \
        " mpr:main -resize '800x>' -quality 80 -interlace Plane -strip -write /tmp/800.jpg +delete" \
        " mpr:main -resize '600x>' -quality 80 -interlace Plane -strip -write /tmp/600.jpg +delete" \
        " mpr:main -resize '200x>' -quality 80 -interlace Plane -strip -write /tmp/200.jpg +delete" \
        " mpr:main -thumbnail '100x100' /tmp/100.jpg".format(filename))

    print( "create_thumbnails_mpr_optimized completed in {} seconds".format(time.time() - start))
    
    thumbs =  [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs



def create_thumbnails_mpr_optimized_new(filename):
    start = time.time()
    
    # var = "convert /tmp/b6b262a33e594b99b2375f6b1b96d72d.jpg -resize '1600x>' -quality 80 -interlace Plane 
    # -strip -write mpr:main +delete mpr:main -write ./1600.jpg +delete mpr:main -resize '800x>' 
    # -quality 80 -interlace Plane -strip ./800.jpg"
    
    # convert /tmp/85e22e088eba4bdc889338d2eeee261e.jpg -resize '1600x>' -quality 80 -interlace Plane -strip -write mpr:main +delete 
    # mpr:main -write 1600.jpg +delete 
    # mpr:main -thumbnail '100x100' 100.jpg

    # we're letting imagemagick read and rotate image, writing to memory (mpr:main)
    # from this copy we're producing the smaller versions we need

    # here's our spec for conversions, this is from create_th_classic
    # os.system("convert {} -resize '1920x1080' -auto-orient -quality 90 -interlace Plane -strip /tmp/hd.jpg".format(filename))
    # os.system("convert {} -resize '1600x1600' -auto-orient -quality 80 -interlace Plane -strip /tmp/1600.jpg".format(filename))
    # os.system("convert {} -resize '800x800' -auto-orient -quality 80 -interlace Plane -strip /tmp/800.jpg".format(filename))
    # os.system("convert {} -resize '600x600' -auto-orient -quality 80 -interlace Plane -strip /tmp/600.jpg".format(filename))
    # os.system("convert {} -resize '400x400' -auto-orient -quality 80 -interlace Plane -strip /tmp/400.jpg".format(filename))
    # os.system("convert {} -resize 'x400' -auto-orient -quality 80 -interlace Plane -strip /tmp/h400.jpg".format(filename))
    # os.system("convert {} -resize '400x' -auto-orient -quality 80 -interlace Plane -strip /tmp/w400.jpg".format(filename))
    # os.system("convert {} -resize '200x200' -auto-orient -quality 80 -interlace Plane -strip /tmp/200.jpg".format(filename))
    # os.system("convert {} -thumbnail '100x100' -auto-orient /tmp/100.jpg".format(filename))
    # os.system("convert {} -thumbnail 100x100^ -gravity center -extent 100x100 -auto-orient /tmp/sq100.jpg".format(filename))
    #
    # this is most likely too many versions, and in too small resolutions. Consider an iphone screen to be ~2500x2500 pixels today
    # however, a reason to send smaller images is both available bandwidth on the client side (think 4G or worse, hotel wifi)
    # 
    # TODO: No reason to upsize images that are smaller than the resolutions we need. We need to both identify this
    # and handle throughout the system to pick the best possible resolution. Also consider graphics with transparency
    # should be rendered on a surface that identifies them as such.

    os.system("convert {} -resize '1600x>' -quality 80 -interlace Plane -strip -write mpr:main +delete" \
        " mpr:main -write /tmp/1600.jpg +delete" \
        " mpr:main -resize '800x>' -quality 80 -interlace Plane -strip -write /tmp/800.jpg +delete" \
        " mpr:main -resize '600x>' -quality 80 -interlace Plane -strip -write /tmp/600.jpg +delete" \
        " mpr:main -resize '200x>' -quality 80 -interlace Plane -strip -write /tmp/200.jpg +delete" \
        " mpr:main -thumbnail '100x100' /tmp/100.jpg".format(filename))

    print ("create_thumbnails_mpr_optimized completed in {} seconds".format(time.time() - start))
    
    thumbs =  [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs

    


def create_thumbnails(filename):
    print( "Creating thumbnails")

    # TODO: When done with v-max and h-max variants, revert to using mpr-optimized function
    
    if debugMode == True:
        thumbs = create_thumbnails_classic(filename)
        #thumbs = create_thumbnails_classic_optimized(filename)
        #thumbs = create_thumbnails_mpr(filename)
        #thumbs = create_thumbnails_mpr_optimized(filename)
    else:
        #thumbs = create_thumbnails_mpr_optimized(filename) # assuming this is the fastest way until tests run
        thumbs = create_thumbnails_classic(filename)

    return thumbs



# #####################################################################
#
# Thumbnail upload to the pv-store container
#
 
def upload_blob(filename, url, account_key, inlineFlag=False):
    bc = BlobClient.from_blob_url(url, account_key)

    try:
        bc.get_blob_properties()
        print( "Blob {} already exists, deleting".format(url))
        bc.delete_blob()
    except:
        None

    start = time.time()
    with open(filename, "rb") as data:
        # flags = {'Content-Disposition' : 'attachment '}
        # if inlineFlag:
        #     flags['Content-Disposition'] = 'inline'
        settings = ContentSettings(content_type="image/jpeg", content_disposition="inline")
        bc.upload_blob(data, blob_type="BlockBlob", content_settings=settings)

    print( "Uploaded {} in {} seconds".format(filename, time.time()-start))



def upload_thumbnails(thumbs, instance_name, account_key, short_id):
    th_url_list = []

    for t in thumbs:
        try:
            qualifier = t[t.rfind('/')+1:]
            url = "https://{}.blob.core.windows.net/pv-store/{}_{}".format(instance_name, short_id, qualifier)
            print( "Uploading: " + t + " to " + url)
            upload_blob(t, url, account_key, inlineFlag=True)
            th_url_list.append(url)
        except Exception as ex:
            print( "Failed to upload " + t + ": " + ex)

    return th_url_list



# #####################################################################
#
# Blob download management
#

def download_blob(url, extension, account_key):
    bc = BlobClient.from_blob_url(url, account_key)
    #print( bc.get_blob_properties())

    tempFileName = "/tmp/" + uuid.uuid4().hex + "." + extension
    print( "Using temp file " + tempFileName)

    try:
        start = time.time()
        print( "Downloading " + url)
        with open(tempFileName, "wb") as my_blob:
            download_stream = bc.download_blob(None, None)
            my_blob.write(download_stream.readall())
        print( "Download completed in {} seconds".format(time.time() - start))
    except Exception as ex:
        print( "Error downloading blob: " + ex)
        
    return tempFileName



# #####################################################################
#
# Event handling
#

def post_new_file_event(file_record):
    try:
        pass
    except Exception as ex:
        print("Cannot post new file event " + ex)


def post_new_folder_event(folder_record):
    try:
        pass
    except Exception as ex:
        print("Cannot post new folder event " + ex)



# #####################################################################
#
# Record handling
#

def create_file_record(url, unique_id, partition_key, short_id, name, extension, relative_path, exifString, xmpString, url_list, md5, sha256, instance_name, account_key):
    start = time.time()

    utcnow = datetime.datetime.utcnow().isoformat()

    # insert the file into the forest, make sure we have a folder to place it on (files are leaves, folders make trees)
    # todo push new folder events if creating new folders
    conn_str = "DefaultEndpointsProtocol=https;AccountName={};AccountKey={};EndpointSuffix=core.windows.net".format(instance_name, account_key)
    root = foldermodel.CreateFolderTreeFromFlatFolderList( foldermodel.LoadAllFoldersFromAzureTable(conn_str) )
    folder = foldermodel.FindFolderByPath(root, relative_path)
    if folder is None:
        folder = foldermodel.AddFolderToModelAndDatabaseRecursive(root, relative_path, conn_str)

    # Each ingested (and successfully processed) file has a unique record containing
    # information, list of previews, 
    file_record = {
        'PartitionKey': partition_key,      # using tree structure for partition key a good idea? #possiblybadidea #possiblygoodidea
        'RowKey': short_id,                 # using unique file name for key a good idea? #badidea #mustbeuniqueinpartition
        'state': 'done',
        'folder_id': folder.id,
        'pvs' : json.dumps(url_list),       # json list of preview urls
        'md5' : md5,                        # md5 checksum of total file binary data at ingestion time
        'sha256' : sha256,                  # sha256 checksum of total file binary data at ingestion time
        'exif' : exifString,                # exif dumped as json by imagemagick
        'xmp' : xmpString                   # if exif identified APP1 data, xmp dump in xml by imagemagick
    }

    table_service = TableService(account_name=instance_name, account_key=account_key)
    table_service.merge_entity('files', file_record)
    

    print( "file_record inserted in {} sec".format(time.time()-start))

    # Change record to folder facing
    # TODO: Strip large metadata blocks and keep info needed for UIs

    file_record["PartitionKey"] = relative_path.replace("/", "%2F")
    file_record['item_type'] = 'file'
    table_service.insert_or_replace_entity('folders', file_record)

    # Ensure we have folder records for the entire path
    # TODO: Optimization; Check if the final folder exists, if so, skip step (we know all higher level paths have been created too)
    
    folder_struct = relative_path.split("/")

    # partition keys cannot have / in them, this is the best I can come up with atm
    folder_struct[0] = "%2F" # path starts with slash, will have empty slot first, replace with /
    last_folder = folder_struct[0] # weird exception case, root refers to itself as parent, but easy to check for later

    for folder_name in folder_struct:
        if len(folder_name) == 0: # ignore empty paths, tolerate e.g. folder1//folder2/folder3/
            continue
        
        folder_record = {
            'PartitionKey': last_folder,
            'RowKey': folder_name,
            'created_time': utcnow,
            'modified_time': utcnow,
            'nf_flag': True,
            'nf_time': utcnow,
            'item_type': 'folder'
        }
        
        if len(folder_name) > 3: # special handling of root
            last_folder = last_folder + "%2F" + folder_name

        # if folder already exist, we will fail, remove the creation properties and
        # try a merge operation (that should work unless service is down)
        try:
            table_service.insert_entity('folders', folder_record)
            post_new_folder_event(folder_record)
        except:
            folder_record.pop('created_time')
            table_service.insert_or_merge_entity('folders', folder_record)

    
    
    # create the leaves entry
    leaf_record = {
        'PartitionKey': folder.id,          # the folder this file is in (branch of tree in forest)
        'RowKey': short_id,
        'state': 'done',                    # all proc done
        'uid': unique_id,                   # globally uniqueId
        'url': url,                         # master blob url
        'name': name,                       # filename
        'ext' : extension,                  # file extension
        'path' : relative_path,             # path / folder file lives in
        'it': utcnow,                       # ingestion_time
        'created_time' : utcnow,            # file creation time, using now, TODO: pick up file metadata if provided in upload
        'modified_time' : utcnow,           # file mod time, using now, TODO: pick up file metadata if provided in upload
        'pvs' : json.dumps(url_list),       # json list of preview urls
        'md5' : md5,                        # md5 checksum of total file binary data at ingestion time
        'sha256' : sha256,                  # sha256 checksum of total file binary data at ingestion time
        'exif' : exifString,                # exif dumped as json by imagemagick
        'xmp' : xmpString                   # if exif identified APP1 data, xmp dump in xml by imagemagick
    }

    table_service.insert_or_replace_entity('leaves', leaf_record)

    # Ready to notify everyone there's a new file in town
    post_new_file_event(file_record)

    # TODO: Post message to pubsub as well for realtime updates of clients

    # PartitionKey    RowKey
    # /               /                 < Do we need this level at all?
    # /               subfolder1
    # /               subfolder2
    # /subfolder1     subfolder1-1



# #####################################################################
#
# Image handling
#

class FileTypeValidationException(Exception):
    pass



def identify_image(file_name):
    try:
        start = time.time()
        cmd = "identify -ping -format \"%m\" {}".format(file_name)
        output = subprocess.check_output(cmd, shell=True)
        print( "File {} identified as: ".format(file_name), output)
        print( "identify_image completed in ", time.time()-start)
        return output.decode()
    except CalledProcessError as ex:
        print( "Error identifying image: ", ex.message)
        return None


def extract_exif(file_name):
    try:
        start = time.time()
        cmd = "convert -ping {} json:".format(file_name)
        output = subprocess.check_output(cmd, shell=True)
        print( "extract_exif completed in ", time.time()-start)
        return output.decode()
    except CalledProcessError as ex:
        print( "Error extracting exif information from: ", ex.message)
        return None



def extract_xmp(file_name):
    try:
        start = time.time()
        cmd = "convert -ping {} XMP:-".format(file_name)
        output = subprocess.check_output(cmd, shell=True)
        print( "extract_xmp completed in ", time.time()-start)
        return output.decode()
    except CalledProcessError as ex:
        print( "Error extracting xmp data from: ", ex.message)
        return None



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

    print( "checksums: md5(", md5.hexdigest(), "), sha256(", sha256.hexdigest(), ")")
    print( "create_file_checksums completed in {} seconds".format(time.time()-start))
    return md5.hexdigest(), sha256.hexdigest()



def _handle_image_generic(url, unique_id, partition_key, short_id, temporary_file_name, name, extension, relative_path, instance_name, account_key):
    thumbs = None

    try:
        # extract metadata

        exif = None
        exifString = extract_exif(temporary_file_name)
        exif = json.loads(exifString)
        
        # file haz xmp metadata?
        
        xmp = None
        if "image" in exif and "profiles" in exif["image"] and "xmp" in exif["image"]["profiles"]:
            print ("Xmp identified, extracting from file ", temporary_file_name)
            xmp = extract_xmp(temporary_file_name)
        else:
            print( "Exif did not indicate app1/xmp data in file ", temporary_file_name)

        # file haz iptc?

        if "image" in exif and "profiles" in exif["image"] and "iptc" in exif["image"]["profiles"]:
            print( "File has iptc metadata, fyi only, not extracting in file ", temporary_file_name)

        # render previews

        thumbs = create_thumbnails(temporary_file_name)
        print( "Thumbnails created: {}".format(thumbs))
        url_list = upload_thumbnails(thumbs, instance_name, account_key, short_id)

        # calculate checksums

        print( "Calculating checksums of original file")
        md5, sha256 = create_file_checksums(temporary_file_name)

        # done the work, create the file record

        print( "Creating master file record")
        create_file_record(url, unique_id, partition_key, short_id, name, extension, relative_path, exifString, xmp, url_list, md5, sha256, instance_name, account_key)

    finally:
        if not debugMode and thumbs is not None:
            for t in thumbs:
                os.remove(t)



def handle_jpeg_image(url, unique_id, partition_key, short_id, temporary_file_name, name, extension, relative_path, instance_name, account_key):
    thumbs = None

    try:
        # validate the file type
        img_type = identify_image(temporary_file_name)
        if not img_type == "JPEG":
            raise FileTypeValidationException("{} ext .jpg is not identified as JPEG.".format(temporary_file_name))

        # handle image
        _handle_image_generic(url, unique_id, partition_key, short_id, temporary_file_name, name, extension, relative_path, instance_name, account_key)

    except Exception as ex:
        print ("handle_image exception: ", ex)
        raise ex
        # TODO: if we fail here, consider tainted and ask infra to recycle container?
        # can do by setting global stopSignal = True or using exit(), unsure of best approach




def handle_generic_file(url, unique_id, partition_key, short_id, temporary_file_name, name, extension, relative_path, instance_name, account_key):
    thumbs = None

    try:
        # calculate checksums

        print( "Calculating checksums of original file")
        md5, sha256 = create_file_checksums(temporary_file_name)

        # done the work, create the file record

        print( "Creating master file record")
        create_file_record(url, unique_id, partition_key, short_id, name, extension, relative_path, None, None, None, md5, sha256, instance_name, account_key)


    except Exception as ex:
        print( "handle_generic_file exception: ", ex)
        raise ex



# #####################################################################
#
# Message handling
# This is effectively our main() function, picking up messages
# of new files ingested into the store. Based on extension
# it will delegate to the correct handling proc, currently
# only handling JPG files, but this will expand to
# more file formats as the project moves on
#
# See Readme and docs on https://github.com/chrfrenning/ironviper
# for full understanding of the system architecture
# and what is handled in different workers (currently only one
# worker in action, will expand in future)
#

def create_orphan_record(url, unique_id, partition_key, short_id, instance_name, account_key):
    start = time.time()
    utcnow = datetime.datetime.utcnow().isoformat()

    print( "Creating orphan record")

    # Each ingested (and successfully processed) file has a unique record containing
    # information, list of previews, 
    orphan_record = {
        'PartitionKey': partition_key,          # using tree structure for partition key a good idea? #possiblybadidea #possiblygoodidea
        'RowKey': short_id,                     # lookup key for this asset
        'uid': unique_id,                       # globally uniqueId
        'url': url,                             # original asset url
        'it': utcnow                            # ingestion_time
    }

    table_service = TableService(account_name=instance_name, account_key=account_key)
    table_service.insert_or_replace_entity('orphans', orphan_record)

    print( "orphan_record inserted in {} sec".format(time.time()-start))



def delete_orphan_record(partition_key, short_id, instance_name, account_key):
    start = time.time()

    table_service = TableService(account_name=instance_name, account_key=account_key)
    table_service.delete_entity('orphans', partition_key, short_id)

    print( "delete_orphan_record completed in {} sec".format(time.time()-start))


def create_new_file_record(url, unique_id, partition_key, short_id, name, extension, relative_path, ingestion_time, created_time, modified_time, instance_name, account_key):
    start = time.time()
    print( "Creating initial file record, state 'new'")

    file_record = {
        'PartitionKey': partition_key,      # using tree structure for partition key a good idea? #possiblybadidea #possiblygoodidea
        'RowKey': short_id,                 # using unique file name for key a good idea? #badidea #mustbeuniqueinpartition
        'state': 'new',                     # initial state
        'uid': unique_id,                   # globally uniqueId
        'url': url,                         # master blob url
        'name': name,                       # filename
        'ext' : extension,                  # file extension
        'path' : relative_path,             # path / folder file lives in
        'it': ingestion_time,               # ingestion_time
        'created_time' : created_time,      # file creation time, using now, TODO: pick up file metadata if provided in upload
        'modified_time' : modified_time     # file mod time, using now, TODO: pick up file metadata if provided in upload
    }

    table_service = TableService(account_name=instance_name, account_key=account_key)
    table_service.insert_or_replace_entity('files', file_record)

    print( "new file_record inserted in {} sec".format(time.time()-start))



def handle_new_file(url, name, relative_path, extension, instance_name, account_key):
    # create id's for this file
    unique_id = uuid.uuid4().hex
    partition_key = shortuuid.random(length=3)
    short_id = partition_key + '-' + shortuuid.random(length=7)
    ingestion_time = datetime.datetime.utcnow().isoformat()
    ingestion_count = 1

    # check if metadata has been set on this blob
    bc = BlobClient.from_blob_url(url, account_key)
    props = bc.get_blob_properties()
    print (props)
    metadata = props.metadata
    if "unique_id" in metadata:
        unique_id = metadata["unique_id"] # TODO: validate that the pattern is acceptable
    if "short_id" in metadata:
        short_id = metadata["short_id"] # TODO: validate that the pattern is acceptable
        partition_key = short_id.split('-')[0]
    if "ingestion_count" in metadata:
        ingestion_count = int(metadata["ingestion_count"]) + 1

    created_time = datetime.datetime.utcnow().isoformat()
    if "created_time" in metadata:
        created_time = metadata["created_time"] # TODO: validate that the pattern is acceptable

    modified_time = datetime.datetime.utcnow().isoformat()
    if "modified_time" in metadata:
        modified_time = metadata["modified_time"] # TODO: validate that the pattern is acceptable

    # update the metadata for this blob
    bc.set_blob_metadata({
        "unique_id": unique_id, 
        "short_id": short_id,
        "ingestion_count": str(ingestion_count)
        })

    # log what we have now
    print( "Unique ids: unique_id: {}, partition_key: {}, short_id: {}".format(unique_id, partition_key, short_id))

    # create orphan record in case the ingestion process breaks
    # the orphan record will be used to clean up any stray data in case we cannot
    # complete the process and get left in-between

    # TODO: lookup orphan message, clean up, and take protective action
    # we must treat the file as a generic file and mark it invalid
    # to avoid processing it over and over again

    create_orphan_record(url, unique_id, partition_key, short_id, instance_name, account_key)

    # create the initial file record

    create_new_file_record(
        url,
        unique_id,
        partition_key,
        short_id,
        name,
        extension,
        relative_path,
        ingestion_time,
        created_time,
        modified_time,
        instance_name,
        account_key
    )

    # TODO: manage rest of process based on extension
    # TODO: use identify -verbose <fn> to get info on file and validate
    # TODO: extract exif and xmp metadata

    tempFileName = download_blob(url, extension, account_key)

    try:
        if extension == "jpg" or extension == "jpeg":
            handle_jpeg_image(url, unique_id, partition_key, short_id, tempFileName, name, extension, relative_path, instance_name, account_key)
        else:
            print( "Don't recognize extension, handling as generic file")
            handle_generic_file(url, unique_id, partition_key, short_id, tempFileName, name, extension, relative_path, instance_name, account_key)
    except FileTypeValidationException as ftvex:
        # TODO: Mark file as invalid in table, alt treat as generic file type
        pass
    finally:
        if not debugMode and tempFileName is not None:
            os.remove(tempFileName)

    # we're done, clean up the orphan tracking record

    delete_orphan_record(partition_key, short_id, instance_name, account_key)



def handle_deleted_file(url, name, extension, instance_name, account_key):
    # TODO: Decide best approach to handle situations when admin (or some process or something else?)
    # deletes files in the main blob store.
    # 1. Do we just comply and delete the file from the system?
    # 2. Do we mark our record as deleted, and offer features around this?
    # 3. Do we just operate with a 'broken' link - it won't have any effect until anyone wants to download the original file
    pass



def handle_message(json_message, instance_name, account_key):
    url = json_message["data"]["url"]
    print( "Starting file processing of " + url)

    # parse url

    fn = urlparse(url).path
    extension = fn[fn.rfind('.')+1:].lower() # convert to lowercase, see switch below
    name = fn[fn.rfind('/')+1:fn.rfind('.')]
    #name = fn[fn.rfind('/')+1:]
    
    path_start = "file-store"
    relative_path = fn[fn.find(path_start)+len(path_start):]
    relative_path = relative_path[:-(len(name)+len(extension)+2)] # plus one for the dot (.jpg), plus one for final slash (/)
    if len(relative_path) == 0:
        relative_path = "/"

    print( "Pathinfo: " + fn + ", " + name + ", " + extension + "," + relative_path)

    # type of message?
    
    event_type = json_message["eventType"]
    print( "Event type: ", event_type)

    if event_type == "Microsoft.Storage.BlobDeleted":
        handle_deleted_file(url, name, extension, instance_name, account_key)
    elif event_type == "Microsoft.Storage.BlobCreated":
        handle_new_file(url, name, relative_path, extension, instance_name, account_key)
    else:
        if debugMode == True:
            raise Exception("Unknown event type ({}).".format(event_type))
        else:
            print( "Unknown event type ({}), ignoring message and deleting.".format(event_type))



def dequeue_messages(config_instance_name, config_account_key):
    conn_str = "DefaultEndpointsProtocol=https;AccountName={};AccountKey={};EndpointSuffix=core.windows.net".format(config_instance_name, config_account_key)
    
    queue_service = QueueClient.from_connection_string(conn_str, "extract-queue")

    # Handle each new message
    messages = queue_service.receive_messages(messages_per_page=1)
    #messages = queue_service.peek_messages(1) # just for easier debugging

    messages_handled = 0
    for msg in messages:

        try:
            start = time.time()
            message = json.loads(base64.b64decode(msg.content))
            # TODO: bring message along so that we can update it to keep it reserved until we're done
            # all thumbnail resizing is making us pass 30 seconds and we loose the msg
            handle_message(message, config_instance_name, config_account_key)
        
            if debugDisableMessageDeque == False:
                queue_service.delete_message(msg)
            else:
                print( "Debug mode, not removing message from queue.")

            print( "Message handled in {} seconds.".format(time.time()-start))
            messages_handled += 1

            if stopSignal == True:
                return messages_handled

        except Exception as ex:
            print( "Error handling message ({})".format(msg.content))
            print( "Exception: " + ex)

        finally:
            # something on every iteration?
            f = 1
    
    return messages_handled



# #####################################################################
#
# Configuration management
#
# Configuration is for now in a toml file created by the
# setup.sh script that deployes the application.
# TODO: Must be switched to environment variables and central
# app configuration as this worker is moved into a container.
#
 
def load_configuration():
    # this depends on whether we're in a docker container
    # or development environment
    # TODO: Consider how to use keyvault in this

    cloud_instance_name = None
    account_key = None
    event_endpoint = None
    event_key = None

    if os.getenv('INSTANCE_NAME', 'n/a') == 'n/a':
        print( "Container envirnoment variable not found, trying to load settings from config file")

        # Load config to know where to talk
        configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
        configuration = toml.load(configuration_file_name)

        # Read configuration parameters
        cloud_instance_name = configuration["instance_name"]
        account_key = configuration["storage_key"] 
        event_endpoint = configuration["eventgrid_endpoint"] 
        event_key = configuration["eventgrid_key"] 
    else:
        cloud_instance_name = os.environ['INSTANCE_NAME']
        account_key = os.environ["STORAGE_KEY"] 
        event_endpoint = os.environ["EVENT_ENDPOINT"] 
        event_key = os.environ["EVENT_KEY"] 

    return cloud_instance_name, account_key



# #####################################################################
#
# SIGTERM handling for graceful shutdown of pods
#
 
def receiveSigTermSignal(signalNumber, frame):
    print('Received stop signal {}, completing current job then stopping. '.format(signalNumber))
    global stopSignal
    stopSignal = True
    return
    


# #####################################################################
#
# Wire up the magic!
#
 
def main():
    random.seed()

    # Check if we're in development mode
    if os.environ.get("DEBUG", "0") == "1":
        global debugMode
        debugMode = True
        print("Running in Debug mode")

    if os.environ.get("DISABLEDEQUES", "0") == "1":
        global debugDisableMessageDeque
        debugDisableMessageDeque = True
        print("Not dequeuing messages, infinite loop coming up :)")

    if os.environ.get("PRODUCTION", "0") == "1":
        global prodMode
        prodMode = True
        print("Running in Production mode")

    if prodMode == False and debugMode == False:
        print("Neither PRODUCTION=1 nor DEBUG=1 environment variables set; stopping.")
        exit(1)

    # Shut me down with sigterm
    print( "New file handling worker started, pid is ", os.getpid(), " send sigterm with 'kill -{} <pid>' or CTRL-C to stop me gracefully.".format(signal.SIGTERM))
    signal.signal(signal.SIGTERM, receiveSigTermSignal)
    signal.signal(signal.SIGINT, receiveSigTermSignal)

    # Load configuration, we need instance name to find our storage account
    # where the queues and containers are
    cloud_instance_name, account_key = load_configuration()

    # Query the queue for new files arrived
    last_message_handled = time.time()

    try:
        while True:
            print( "Polling queue...")
            messages_handled = dequeue_messages(cloud_instance_name, account_key)

            if stopSignal == True:
                print("Stop signal received, aborting polling and checking out.")
                exit(0)

            # if idle for > X minutes, return to shut down the container
            if messages_handled > 0:
                last_message_handled = time.time()
            else:
                max_seconds = 60*2
                if time.time() - last_message_handled > max_seconds and not debugMode: # 5 minutes delay maximum
                    print( "Idle for more than {} minutes, shutting down converter process".format(max_seconds/60))
                    exit(0)

            # Wait a random time before checking again
            time.sleep( random.randrange(1,3) )

    except Exception as ex:
        print( "An error occurred during message management. " + ex)
        exit(1)



if __name__ == "__main__":
    print( "Version: ironviper/{}".format(version))
    main()