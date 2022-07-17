#!/usr/bin/env python3
import os
import sys
import toml
import argparse
import json
import uuid
import requests
from datetime import datetime

def post_event(endpoint, accesskey, typestr, subject, data={}):
    id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    events=[
            {
                'id' : id,
                'subject' : subject,
                'data': data,
                'eventType': typestr,
                'eventTime': timestamp.isoformat(),
                'dataVersion': 1
            }
        ]
    
    headers = { 'aeg-sas-key' : accesskey, 'Content-Type' : 'application/json' }
    r = requests.post(endpoint, headers=headers, data=json.dumps(events))
    
    if not 200 >= r.status_code < 300:
        raise Exception(r.content)

def load_configuration():
    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
    configuration = toml.load(configuration_file_name)

    eventgrid_endpoint = configuration["eventgrid_endpoint"]
    eventgrid_key = configuration["eventgrid_key"]

    return eventgrid_endpoint, eventgrid_key



parser = argparse.ArgumentParser(description='Trigger an ironviper event')
parser.add_argument('-t', '--type', help="The event type you want to post.")
parser.add_argument('-s', '--subject', help="The event subject you want to post.")

args = parser.parse_args()
endpoint, accesskey = load_configuration()
res = post_event(endpoint, accesskey, args.type, args.subject, None)