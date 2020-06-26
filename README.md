# ironviper

Goal: provide very cost efficient cloud photo storage with some clever features

What? Image conversion at scale using imagemagick, docker containers, and cloud power (azure)

Note! this project is at very early stage, not much functioning yet.


## status

Current status is that resource provisioning (deploy_azure.sh) is working, and manual uploads of files to 'file-store' container will result in thumbs and previews generated if running 'python converter.py' on some instance somewhere. #notforthefaintofheart


## how to get started

1. You need an Azure subscription.
1. Fire up the [Azure Cloud Shell](https://shell.azure.com/) using Bash.
1. Issue the command below to build the infrastructure and start up the latest version of the app

```
    
    curl -sL https://raw.githubusercontent.com/chrfrenning/ironviper/master/setup.sh | bash 
    
```

1. This will take a few minutes, then you're ready to go!
1. In lack of the worker container, here's how to test ingestion, metadata extraction and preview creation
    1. Fire up a linux instance somewhere
    1. Copy the configuration.toml from your azure shell instance
    1. Run ./converter/setup.sh and then python converter.py to keep ingestion worker going

### debug mode

Set environment variable DEBUG=1 for additional information, tests, and diagnostics


### issues

I'll use github issues soon to track things that are not working, for now we have this list

1. Digital camera images are not auto-rotated
1. Error handling, need mechanism to avoid orphaned trouble files, both masters and previews can be orphaned today
1. Code consistency is like... it took four hours to write #needscleanup
1. Tons of stuff is missing


### plan

1. Containerize converter module
1. Deployment and auto-scaling of containers for ingestion
1. Infrastructure to scale converter containers, from 0 to massive (focus on cost-optimization, goal is 0 cost apart from storage when no activity)
1. Web frontend to display ingested files
1. Split setup.sh into 1) default provision in azure only 2) and optional setup local dev and debug environment