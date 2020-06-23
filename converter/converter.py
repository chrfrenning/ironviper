import json
import toml
import os
import uuid
import time
import base64
import signal
import random
import subprocess
from urlparse import urlparse
from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient



# #####################################################################
#
# Global variables (hell yeah)

stopSignal = None
debugMode = False



# #####################################################################
#
# Thumbnail creation using imagemagick
#

def create_thumbnails_classic(filename):
    start = time.time()

    os.system("convert {} -resize '1600x>' -quality 80 -interlace Plane -strip /tmp/1600.jpg".format(filename))
    os.system("convert {} -resize '800>' -quality 80 -interlace Plane -strip /tmp/800.jpg".format(filename))
    os.system("convert {} -resize '600>' -quality 80 -interlace Plane -strip /tmp/600.jpg".format(filename))
    os.system("convert {} -resize '400>' -quality 80 -interlace Plane -strip /tmp/400.jpg".format(filename))
    os.system("convert {} -resize '200>' -quality 80 -interlace Plane -strip /tmp/200.jpg".format(filename))
    os.system("convert {} -thumbnail '100x100' /tmp/100.jpg".format(filename))

    print "create_thumbnails_classic completed in {} seconds".format(time.time() - start)

    thumbs =  [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs
    
    
    
def create_thumbnails_classic_optimized(filename):
    start = time.time()

    os.system("convert {} -resize '1600x>' -quality 80 -interlace Plane -strip /tmp/1600.jpg".format(filename))
    os.system("convert /tmp/1600.jpg -resize '800>' -quality 80 -interlace Plane -strip /tmp/800.jpg".format(filename))
    os.system("convert /tmp/1600.jpg -resize '600>' -quality 80 -interlace Plane -strip /tmp/600.jpg".format(filename))
    os.system("convert /tmp/800.jpg -resize '400>' -quality 80 -interlace Plane -strip /tmp/400.jpg".format(filename))
    os.system("convert /tmp/800.jpg -resize '200>' -quality 80 -interlace Plane -strip /tmp/200.jpg".format(filename))
    os.system("convert /tmp/800.jpg -thumbnail '100x100' /tmp/100.jpg".format(filename))

    print "create_thumbnails_classic_optimized completed in {} seconds".format(time.time() - start)

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
    
    print "create_thumbnails_mpr completed in {} seconds".format(time.time() - start)
    
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

    print "create_thumbnails_mpr_optimized completed in {} seconds".format(time.time() - start)
    
    thumbs =  [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/600.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]
    return thumbs



def create_thumbnails(filename):
    print "Creating thumbnails"

    if debugMode == True:
        thumbs = create_thumbnails_classic(filename)
        thumbs = create_thumbnails_classic_optimized(filename)
        thumbs = create_thumbnails_mpr(filename)
        thumbs = create_thumbnails_mpr_optimized(filename)
    else:
        thumbs = create_thumbnails_mpr_optimized(filename) # assuming this is the fastest way until tests run

    return thumbs



# #####################################################################
#
# Thumbnail upload to the pv-store container
#
 
def upload_blob(filename, url, account_key):
    bc = BlobClient.from_blob_url(url, account_key)

    try:
        bc.get_blob_properties()
        print "Blob {} already exists, deleting".format(url)
        bc.delete_blob()
    except:
        None

    start = time.time()
    with open(filename, "rb") as data:
        bc.upload_blob(data, blob_type="BlockBlob")

    print "Uploaded {} in {} seconds".format(filename, time.time()-start)



def upload_thumbnails(thumbs, name, instance_name, account_key):
    for t in thumbs:
        try:
            qualifier = t[t.rfind('/')+1:]
            url = "https://{}.blob.core.windows.net/pv-store/{}_{}".format(instance_name, name, qualifier)
            print "Uploading: " + name + t + " to " + url
            upload_blob(t, url, account_key)
        except Exception as ex:
            print "Failed to upload " + t + ": " + ex.message


# #####################################################################
#
# Blob download management
#

def download_blob(url, account_key):
    bc = BlobClient.from_blob_url(url, account_key)
    #print bc.get_blob_properties()

    tempFileName = "/tmp/" + uuid.uuid4().hex + ".jpg"
    print "Using temp file " + tempFileName

    try:
        start = time.time()
        print "Downloading " + url
        with open(tempFileName, "wb") as my_blob:
            download_stream = bc.download_blob(None, None)
            my_blob.write(download_stream.readall())
        print "Download completed in {} seconds".format(time.time() - start)
    except Exception as ex:
        print "Error downloading blob: " + ex.message
        
    return tempFileName



# #####################################################################
#
# Image handling
#
 
def generic_handle_image(temporary_file_name, name, instance_name, account_key):
    thumbs = None

    try:
        thumbs = create_thumbnails(temporary_file_name)
        print "Thumbnails created: {}".format(thumbs)
        upload_thumbnails(thumbs, name, instance_name, account_key)

    finally:
        if not debugMode and thumbs is not None:
            for t in thumbs:
                os.remove(t)



def identify_image(file_name):
    output = subprocess.check_output("identify {}".format(file_name), shell=False)
    print("Identify results: ", output)
    return output



def handle_jpeg_image(temporary_file_name, name, instance_name, account_key):
    thumbs = None

    try:
        # validate the file type
        # img_type = identify_image(temporary_file_name)

        # handle image
        generic_handle_image(temporary_file_name, name, instance_name, account_key)

    except Exception as ex:
        print("handle_image exception: ", ex.message)
        # todo: if we fail here, consider tainted and ask infra to recycle container?
        # can do by setting global stopSignal = True or using exit(), unsure of best approach



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
 
def handle_message(json_message, instance_name, account_key):
    url = json_message["data"]["url"]
    print "Starting file processing of " + url

    # parse url
    fn = urlparse(url).path
    extension = fn[fn.rfind('.')+1:].lower() # convert to lowercase, see switch below
    name = fn[fn.rfind('/')+1:fn.rfind('.')]

    print "Pathinfo: " + fn + ", " + name + ", " + extension
    # todo: manage rest of process based on extension
    # todo: use identify -verbose <fn> to get info on file and validate
    # todo: extract exif and xmp metadata

    tempFileName = None

    try:
        if extension == "jpg":
            tempFileName = download_blob(url, account_key)
            handle_jpeg_image(tempFileName, name, instance_name, account_key)
        else:
            print "Don't know how to handle this file type"
            # TODO: discard file by marking in an unknown table?
    except Exception as ex:
        print "Error handling blob: " + ex.message
    finally:
        if not debugMode and tempFileName is not None:
            os.remove(tempFileName)



def dequeue_messages(config_instance_name, config_account_key):
    conn_str = "DefaultEndpointsProtocol=https;AccountName={};AccountKey={};EndpointSuffix=core.windows.net".format(config_instance_name, config_account_key)
    
    queue_service = QueueClient.from_connection_string(conn_str, "extract-queue")

    # Handle each new message
    messages = queue_service.receive_messages(messages_per_page=1)
    #messages = queue_service.peek_messages(1) # just for easier debugging

    for msg in messages:

        try:
            start = time.time()
            message = json.loads(base64.b64decode(msg.content))
            # todo: bring message along so that we can update it to keep it reserved until we're done
            # all thumbnail resizing is making us pass 30 seconds and we loose the msg
            handle_message(message, config_instance_name, config_account_key)
        
            if not debugMode:
                queue_service.delete_message(msg)
            else:
                print "Debug mode, not removing message from queue."

            print "Message handled in {} seconds.".format(time.time()-start)

            if (stopSignal is not None) and (stopSignal == True):
                return

        except Exception as ex:
            print "Error handling message ({})".format(msg.content)
            print "Exception: " + ex.message

        finally:
            # something on every iteration?
            f = 1



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
    # Load config to know where to talk
    configuration = toml.load("../configuration.toml")

    # Read configuration parameters
    cloud_instance_name = configuration["instance_name"]
    account_key = configuration["account_key"] # TODO: Get from keyvault

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

    # Shut me down with sigterm
    print("New file handling worker started, pid is ", os.getpid(), " send sigterm with 'kill -{} <pid>' or CTRL-C to stop me gracefully.".format(signal.SIGTERM))
    signal.signal(signal.SIGTERM, receiveSigTermSignal)
    signal.signal(signal.SIGINT, receiveSigTermSignal)

    # Load configuration, we need instance name to find our storage account
    # where the queues and containers are
    cloud_instance_name, account_key = load_configuration()

    # Query the queue for new files arrived
    try:
        while True:
            print "Polling queue..."
            dequeue_messages(cloud_instance_name, account_key)

            if (stopSignal is not None) and (stopSignal == True):
                print("Stop signal received, aborting polling and checking out.")
                return

            # Wait a random time before checking again
            time.sleep( random.randrange(1,3) )

    except Exception as ex:
        print "An error occurred during message management. " + ex.message



if __name__ == "__main__":
    main()