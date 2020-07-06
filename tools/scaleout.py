#!/usr/bin/env python2.7
import os
import toml
import sys
import requests
import json

# #####################################################################
#
# Increases active converter containers by one
#
# Enumerates all containers in the resource group, finds first
# with state Terminated and restarts it
#

management_url = "https://management.azure.com/"



def get_token(configuration):
    client_id = configuration["client_id"]
    client_secret = configuration["client_secret"]
    tenant_id = configuration["tenant_id"]

    params = { 'grant_type':'client_credentials', 'client_id':client_id, 'client_secret':client_secret, 'resource':management_url}
    url ="https://login.microsoftonline.com/{}/oauth2/token".format(tenant_id)
    r = requests.post(url, data=params)

    data = json.loads(r.content)
    return data["access_token"]



def main():
    try:
        configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
        configuration = toml.load(configuration_file_name)

        token = get_token(configuration)

        subscription_id = configuration["subscription_id"]
        resource_group = configuration["instance_name"]
        baseurl =  "subscriptions/{}/resourceGroups/{}/".format(subscription_id, resource_group)

        params = {'api-version':'2019-12-01'}
        headers = {'Authorization':'Bearer {}'.format(token)}

        url = management_url + baseurl + "providers/Microsoft.ContainerInstance/containerGroups/"
        r = requests.get(url, headers=headers, params=params)

        data = json.loads(r.content)
        for e in data["value"]:
            r = requests.get(management_url+e["id"], headers=headers, params=params)
            props = json.loads(r.content)

            state = props["properties"]["containers"][0]["properties"]["instanceView"]["currentState"]["state"]
            if state == "Terminated":
                print "Starting container", e["id"]
                startRes = requests.post(management_url+e["id"]+"/start", headers=headers, params=params)
                if 200 <= startRes.status_code < 300:
                    exit(0)
                else:
                    print startRes.status_code, startRes.reason, startRes.content
                    print "Failed, trying next..."

        # no containers started (we would've exited)
        exit(1)

    except Exception as ex:
        print ex.message
        exit(2)



if __name__ == "__main__":
    main()


