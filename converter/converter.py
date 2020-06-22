import json
import toml
import os
from azure.storage.queue import QueueService
from azure.storage.queue import QueueMessageFormat
from azure.storage.blob import BlobServiceClient
from azure.storage.blob import BlobClient

# Load config to know where to talk
configuration = toml.load("../configuration.toml")
cloud_instance_name = configuration["resource_group"]

# TODO: get from keyvault
account_key = "eHxQVP++/kxBQCMCs07sqaHVp2kpYJOUhU32Hu2/u10g/IciUKutRGUhNIA0A58PqoKTaliekZ7WKyKTB9t+2Q=="

# Query the queue for new files arrived
queue_service = QueueService(account_name=cloud_instance_name, account_key='eHxQVP++/kxBQCMCs07sqaHVp2kpYJOUhU32Hu2/u10g/IciUKutRGUhNIA0A58PqoKTaliekZ7WKyKTB9t+2Q==')
queue_service.decode_function = QueueMessageFormat.binary_base64decode

# Handle each new message
messages = queue_service.get_messages('extract-queue')
for msg in messages:
    message = json.loads(msg.content)
    url = message["data"]["url"]
    print url

    bsc = BlobServiceClient.from_connection_string("DefaultEndpointsProtocol=https;AccountName=ironviper00b6e128;AccountKey=eHxQVP++/kxBQCMCs07sqaHVp2kpYJOUhU32Hu2/u10g/IciUKutRGUhNIA0A58PqoKTaliekZ7WKyKTB9t+2Q==;EndpointSuffix=core.windows.net")
    bc = bsc.get_blob_client("file-store", "DSCF8791.JPG")
    # print bc.get_blob_properties()
    
    with open("./temp.jpg", "wb") as my_blob:
        download_stream = bc.download_blob(None, None)
        my_blob.write(download_stream.readall())

    os.system("convert temp.jpg -write mpr:main +delete" \
        " mpr:main -resize \"1600x>\" -quality 80 -interlace Plane -strip -write 1600.jpg +delete" \
        " mpr:main -resize \"800x>\" -quality 80 -interlace Plane -strip -write 800.jpg +delete" \
        " mpr:main -resize \"200x>\" -quality 80 -interlace Plane -strip -write 200.jpg +delete" \
        " mpr:main -thumbnail \"100x100\" -write 100.jpg")

    bc = bsc.get_blob_client("pv-store", "DSCF8791_100.JPG")
    with open("100.jpg", "rb") as data:
        bc.upload_blob(data, blob_type="BlockBlob")
    os.remove("100.jpg")

    bc = bsc.get_blob_client("pv-store", "DSCF8791_200.JPG")
    with open("200.jpg", "rb") as data:
        bc.upload_blob(data, blob_type="BlockBlob")
    os.remove("200.jpg")
    
    bc = bsc.get_blob_client("pv-store", "DSCF8791_800.JPG")
    with open("800.jpg", "rb") as data:
        bc.upload_blob(data, blob_type="BlockBlob")
    os.remove("800.jpg")

    bc = bsc.get_blob_client("pv-store", "DSCF8791_1600.JPG")
    with open("1600.jpg", "rb") as data:
        bc.upload_blob(data, blob_type="BlockBlob")
    os.remove("1600.jpg")

    os.remove("temp.jpg")

    

    # Clean up, TODO: enable this, not using while debugging
    # queue_service.delete_message('extract-queue', message.id, message.pop_receipt)