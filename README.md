# ironviper

Goal: provide very cost efficient cloud photo storage with some clever features

What? Image conversion at scale using imagemagick, docker containers, and cloud power (azure), some search and some frontends

Note! this project is at very early stage, not much functioning yet. Want the nitty-gritty details? [Read the Journal](https://github.com/chrfrenning/ironviper/wiki/Journal).


## status

Current status is that resource provisioning (deploy_azure.sh) is working, and manual uploads of files to 'file-store' container will result in thumbs and previews generated if you run the converter container somewhere. #notforthefaintofheart


## can i test this somehow?

Once more of the project is done, I will set up a public test site so that you can see what this is about without
deploying and running the stuff yourself.


## how to get started

1. You need an Azure subscription.
1. Fire up the [Azure Cloud Shell](https://shell.azure.com/) using Bash.
1. Issue the command below to build the infrastructure and start up the latest version of the app

```
    
    curl -sL https://raw.githubusercontent.com/chrfrenning/ironviper/main/setup.sh | bash 
    
```

1. Fire up a linux instance somewhere, you need docker support
1. Copy the configuration.toml from your azure shell instance (bug! that won't work, you'll need to create it yourself. hints in setup.sh)
1. Run 'export DEBUG=1'
1. Run 'python ./converter/run_docker.py' to start a container with the converter
1. Upload some files using 'python tools/upload.py'
1. Inspect the files table, pv-store to see output


### issues

I'll use github issues soon to track things that are not working, for now we have this list

1. Digital camera images are not auto-rotated
1. Error handling, need mechanism to avoid orphaned trouble files, both masters and previews can be orphaned today
1. Code consistency is like... it took four hours to write #needscleanup
1. Tons of stuff is missing


### plan

1. ~Containerize converter module~
1. ~Scaffold api~
1. ~Ingest test files to storage at setup~ and automate (massive) test file uploads (you can upload a single file with upload.py)
1. ~Create file records for unknown file types, treat anything not explicitly handled as generic file (no metadata, preview, etc)~
1. ~Configure azure functions before deployment, need instance name and keys, plus backend for static serving~
1. Infrastructure to scale converter containers, from 0 to massive (focus on cost-optimization, goal is 0 cost apart from storage when no activity)
1. Handle blob deletions. Don't know how yet, what is sensible? Effectively external deletions, should we respect and delete everything, or should we keep the record and indicate a broken link? #thinkingneeded
1. Calculate perceptual image hashes for de-dupe and extract key metadata for heuristics dedupe process.

1. Web frontend to display ingested files. Headache: choosing frontend framework, react, vue, angular???
1. Split setup.sh into 1) default provision in azure only (it-pro mode) 2) and optional setup local dev and debug environment (pro-dev mode)
1. Handle digital negatives with dcraw (must build imagemagick from source when creating container?)
1. change from python 2 to 3 for converter? consider at a later point, if we want a smaller container image we may have to forgo python anyhow.
1. make a clear-all-data.py tool to wipe storage, tables, and queues for fresh start when dev and debug
