#!/usr/bin/env python3
import toml
import os

configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
configuration = toml.load(configuration_file_name)
account_name = configuration["instance_name"]
account_key = configuration["storage_key"]
event_endpoint = configuration["eventgrid_endpoint"]
event_key = configuration["eventgrid_key"]

os.system("sudo docker build -t ironviper-converter:latest .")
os.system("sudo docker run -it --rm \
    --env INSTANCE_NAME={instance_name} \
    --env STORAGE_KEY={account_key} \
    --env EVENT_ENDPOINT={event_endpoint}  \
    --env EVENT_KEY={event_key} \
    --env PRODUCTION=1 \
    ironviper-converter"
    .format(
        instance_name=account_name, 
        account_key=account_key, 
        event_endpoint=event_endpoint, 
        event_key=event_key))
