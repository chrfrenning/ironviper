# ironviper

Goal: provide very cost efficient cloud photo storage with some clever features

What? Image conversion at scale using imagemagick, docker containers, and cloud power (azure), some search and some frontends

Note! this project is at very early stage, not much functioning yet. Want the nitty-gritty details? [Read the Journal](https://github.com/chrfrenning/ironviper/wiki/Journal).

Are you a photographer? I want to hear from you and learn what you need! DM @chrfrenning on Twitter or email me on christopher@frenning.com or give me a call at +41 (0) 76 518 08 77


## status

Current status is that resource provisioning (setup.sh) is working, and manual uploads of files to 'file-store' container will result in thumbs and previews generated. a very simple web interface will display thumbnails and links to detail page.


## how to get started

1. You need an Azure subscription.
1. Fire up the [Azure Cloud Shell](https://shell.azure.com/) using Bash.
1. Issue the command below to build the infrastructure and start up the latest version of the app

```
    
    curl -sL https://raw.githubusercontent.com/chrfrenning/ironviper/main/setup.sh | bash 
    
```

1. Upload some files using 'python tools/upload.py'
1. Inspect the files+folder tables for fileinfo and metadata, pv-store to see output
1. See url presented at end of setup for very naïve web ui


### plan


1. Read metadata from uploader when ingesting files (org filename, org modified time, client generated hashes)
1. Write system id back to blob as metadata, immediately after getting new file notification. maintain ingestion test counter.
1. Consider: If uploaded file name is GUID, use as basis for internal ids. Creates predictable urls for ingested files. Places restriction on file upload, all files with GUID names must be unique, should not be a big problem? Hmm...
1. Add support for RAW files, extract embedded thumb or best-approach conversion
1. Scaffold react app for ui's
1. ~Split static website and api; debugging not easily viable with current setup~
1. ~Read relative path from blob and store as record field, use for hierarchical structure.~ Need to figure out how to build the folder navigation data structure.
1. ~Containerize converter module~
1. ~Scaffold api~
1. ~Ingest test files to storage at setup~ and automate (massive) test file uploads (you can upload a single file with upload.py)
1. ~Create file records for unknown file types, treat anything not explicitly handled as generic file (no metadata, preview, etc)~
1. ~Configure azure functions before deployment, need instance name and keys, plus backend for static serving~
1. ~Deploy conversion container.~
1. ~Infrastructure to scale converter containers, from 0 to massive. Massive is now 10 instances.~
1. Calculate perceptual image hashes for de-dupe and extract key metadata for heuristics dedupe process.
1. ~Scaffold web frontend to display ingested files.~ Headache: choosing frontend framework, react, vue, angular??? Journal framework decision.
1. ~Split setup.sh into 1) default provision in azure only (it-pro mode) 2) and optional setup local dev and debug environment (pro-dev mode)~
1. set a delete lock on the storage account. important data will be stored here, so we don't want unwanted deletes. 
1. change from python 2 to 3 for converter? consider at a later point, if we want a smaller container image we may have to forgo python anyhow.
1. make a clear-all-data.py tool to wipe storage, tables, and queues for fresh start when dev and debug. Use ARM tag Development: True to authorize this script to run.
1. Handle blob deletions. Don't know how yet, what is sensible? Effectively external deletions, should we respect and delete everything, or should we keep the record and indicate a broken link? #thinkingneeded

## me

Made in ![Swiss Flag](https://chphno.blob.core.windows.net/ironviper-static/switzerland-flag-icon-16.png) by a ![Norwegian Flag](https://chphno.blob.core.windows.net/ironviper-static/norway-flag-icon-16.png). Inspired by the light in alps and fjords + love of quality, chocolate and great food.
