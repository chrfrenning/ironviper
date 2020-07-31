#!/usr/bin/env python2.7
import os
import sys
import toml
import argparse
sys.path.append(os.path.abspath('../libs/python'))
from eventgrid import trigger_event

def load_configuration():
    configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
    configuration = toml.load(configuration_file_name)

    instance_name = configuration["instance_name"]
    storage_key = configuration["storage_key"]
    eventgrid_endpoint = configuration["eventgrid_endpoint"]
    eventgrid_key = configuration["eventgrid_key"]

    return eventgrid_endpoint, eventgrid_key



parser = argparse.ArgumentParser(description='Trigger an ironviper event')
parser.add_argument('-t', '--type', help="The event type you want to post.")
parser.add_argument('-s', '--subject', help="The event subject you want to post.")

args = parser.parse_args()
endpoint, accesskey = load_configuration()
res = post_event(endpoint, accesskey, args.type, args.subject, None)