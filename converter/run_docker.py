import toml
import os

configuration = toml.load("../configuration.toml")
account_name = configuration["instance_name"]
account_key = configuration["account_key"]

os.system("sudo docker build -t ironviper-converter .")
os.system("sudo docker run -it --rm --env INSTANCE_NAME={} --env ACCOUNT_KEY={} ironviper-converter".format(account_name, account_key))
