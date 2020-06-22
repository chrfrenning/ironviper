import json
import toml
import os
import uuid
import time
import base64
from urlparse import urlparse
from azure.storage.queue import QueueClient
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient


def create_thumbnails(filename):
    print "Creating thumbnails"

    start = time.time()
    os.system("convert {} -write mpr:main +delete" \
        " mpr:main -resize \"1600x>\" -quality 80 -interlace Plane -strip -write /tmp/1600.jpg +delete" \
        " mpr:main -resize \"800x>\" -quality 80 -interlace Plane -strip -write /tmp/800.jpg +delete" \
        " mpr:main -resize \"200x>\" -quality 80 -interlace Plane -strip -write /tmp/200.jpg +delete" \
        " mpr:main -thumbnail \"100x100\" -write /tmp/100.jpg null:".format(filename))
    print "Conversion completed in {} seconds".format(time.time() - start)
    return [ "/tmp/1600.jpg", "/tmp/800.jpg", "/tmp/200.jpg", "/tmp/100.jpg" ]



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



def handle_image(temporary_file_name, name, instance_name, account_key):
    thumbs = None

    try:
        thumbs = create_thumbnails(temporary_file_name)
        print "Thumbnails created: {}".format(thumbs)
        upload_thumbnails(thumbs, name, instance_name, account_key)
    finally:
        if thumbs is not None:
            for t in thumbs:
                os.remove(t)



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


def handle_message(json_message, instance_name, account_key):
    url = json_message["data"]["url"]
    print "Starting file processing of " + url

    # parse url
    fn = urlparse(url).path
    extension = fn[fn.rfind('.')+1:].lower()
    name = fn[fn.rfind('/')+1:fn.rfind('.')]

    print "Pathinfo: " + fn + ", " + name + ", " + extension
    # todo: manage rest of process based on extension

    #tempFileName = None

    try:
        if extension == "jpg":
            tempFileName = download_blob(url, account_key)
            handle_image(tempFileName, name, instance_name, account_key)
        else:
            print "Don't know how to handle this file type"
    except Exception as ex:
        print "Error handling blob: " + ex.message
    #finally:
    #    if tempFileName is not None:
    #        os.remove(tempFileName)



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
            handle_message(message, config_instance_name, config_account_key)
        
            queue_service.delete_message(msg)

            print "Message handled in {} seconds.".format(time.time()-start)

        except Exception as ex:
            print "Error handling message ({})".format(msg.content)
            print "Exception: " + ex.message

        finally:
            # something on every iteration?
            f = 1



def load_configuration():
    # Load config to know where to talk
    configuration = toml.load("../configuration.toml")

    # Read configuration parameters
    cloud_instance_name = configuration["instance_name"]
    account_key = configuration["account_key"] # TODO: Get from keyvault

    return cloud_instance_name, account_key



def main():
    cloud_instance_name, account_key = load_configuration()

    # Query the queue for new files arrived
    try:
        while True:
            print "Polling queue..."
            dequeue_messages(cloud_instance_name, account_key)
    except Exception as ex:
        print "An error occurred during message management. " + ex.message



if __name__ == "__main__":
    main()