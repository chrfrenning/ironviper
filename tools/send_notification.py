#!/usr/bin/env python3
import os
import toml
from azure.messaging.webpubsubservice import WebPubSubServiceClient

def load_configuration():
    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
    configuration = toml.load(configuration_file_name)

    return configuration["pubsub_conn"]
    
HUBNAME = "notifications"
pubsub_conn = load_configuration()
service = WebPubSubServiceClient.from_connection_string(connection_string=pubsub_conn, hub=HUBNAME)
service.send_to_all( "yeah!" )