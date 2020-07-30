#!/usr/bin/env python2.7
import os
import toml
import uuid
import json
import argparse
from datetime import datetime
import requests



def load_configuration():
    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
    configuration = toml.load(configuration_file_name)

    instance_name = configuration["instance_name"]
    storage_key = configuration["storage_key"]
    eventgrid_endpoint = configuration["eventgrid_endpoint"]
    eventgrid_key = configuration["eventgrid_key"]

    return eventgrid_endpoint, eventgrid_key



def trigger_event(typestr, subject, data={}):
    endpoint, accesskey = load_configuration()

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
    
    if 200 >= r.status_code < 300:
        return True
    else:
        print("Failed.", r.text)
        return False


parser = argparse.ArgumentParser(description='Trigger an ironviper event')
parser.add_argument('-t', '--type', help="The event type you want to post.")
parser.add_argument('-s', '--subject', help="The event subject you want to post.")

args = parser.parse_args()
res = trigger_event(args.type, args.subject, None)

exit(0) if res == True else exit(1)