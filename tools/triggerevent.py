#!/usr/bin/env python2.7
import os
import toml
import uuid
import argparse
from datetime import datetime
from azure.eventgrid import EventGridClient
from msrest.authentication import TopicCredentials



def load_configuration():
    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
    configuration = toml.load(configuration_file_name)

    instance_name = configuration["instance_name"]
    storage_key = configuration["storage_key"]
    eventgrid_endpoint = configuration["eventgrid_endpoint"]
    eventgrid_key = configuration["eventgrid_key"]

    return eventgrid_endpoint, eventgrid_key



def trigger_event(typestr, subject, payload=""):
    endpoint, accesskey = load_configuration()
    print(endpoint, accesskey)

    credentials = TopicCredentials(accesskey)
    event_grid_client = EventGridClient(credentials)

    id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    print("Created id for this event ", id, "tz", timestamp)

    event_grid_client.publish_events(
        endpoint,
        events=[
            {
                'id' : id,
                'subject' : subject,
                'data': {
                    'key' : 'value',
                    'key2' :'value2'
                },
                'event_type': typestr,
                'event_time': timestamp,
                'data_version': 1
            }
        ]
    )



parser = argparse.ArgumentParser(description='Trigger an ironviper event')
parser.add_argument('-t', '--type', help="The event type you want to post.")
parser.add_argument('-s', '--subject', help="The event subject you want to post.")
parser.add_argument('-p', '--payload', default="", help="Payload for the event.")
#parser.add_argument('-k', '--keeppath', default=False, action="store_true", help="Keep path of uploaded file in blob storage, relative to --path")
#parser.add_argument('-p', '--path', default=None, help="Specify a destination path/subfolder")

args = parser.parse_args()
trigger_event(args.type, args.subject, args.payload)