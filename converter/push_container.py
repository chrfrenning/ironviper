#!/usr/bin/env python3
import toml
import os

configuration_file_name = os.path.dirname(os.path.abspath(__file__)) + "/../configuration.toml"
configuration = toml.load(configuration_file_name)
instance_name = configuration["instance_name"]
registry_url = configuration["registry_url"]


#os.system("az acr build --registry {} --image ironviper-converter:latest .".format(instance_name))
os.system("az container delete -g {} -n {}-converter-00 -y".format(instance_name, instance_name))
os.system("az container create -g {instance_name} -n {instance_name}-converter-00 --cpu 1 --memory 1 \
    --restart-policy OnFailure --image {registry_url}/ironviper-converter:latest --registry-login-server {registry_url} \
        --registry-username {registry_username} --registry-password {registry_password} -e INSTANCE_NAME={instance_name} \
            ACCOUNT_KEY={account_key} EVENT_ENDPOINT={event_grid_endpoint} EVENT_KEY={event_grid_key} PRODUCTION=1"
.format(
    instance_name=instance_name,
    registry_url=registry_url,
    registry_username=configuration["registry_username"],
    registry_password=configuration["registry_password"],
    account_key=configuration["storage_key"],
    event_grid_endpoint=configuration["eventgrid_endpoint"],
    event_grid_key=configuration["eventgrid_key"]
    ))