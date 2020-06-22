# ironviper

Goal: provide very cost efficient cloud photo storage with some clever features

What? Image conversion at scale using imagemagick, docker containers, and cloud power (azure)

Note! this project is at very early stage, not much functioning yet.


## status

Current status is that resource provisioning (deploy_azure.sh) is working, and manual uploads of files to 'file-store' container will result in thumbs and previews generated if running 'python converter.py' on some instance somewhere. #notforthefaintofheart

## next steps

* deployment and auto scaling of containers for conversions
* web ui to display results

## how to get started

1. You need an Azure subscription.
2. Fire up the [Azure Cloud Shell](https://shell.azure.com/) using Bash.
3. Issue the command below to build the infrastructure and start up the latest version of the app

```
    
    curl -sL https://raw.githubusercontent.com/chrfrenning/ironviper/master/setup.sh | bash 
    
```

4. This will take a few minutes, then you're ready to go!
