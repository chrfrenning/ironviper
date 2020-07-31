# ironviper

Goal: provide very cost efficient cloud photo storage with some clever features

What? Image conversion at scale using imagemagick, docker containers, and cloud power (azure), some search and some frontends

Note! this project is at very early stage, not much functioning yet. Want the nitty-gritty details? [Read the Journal](https://github.com/chrfrenning/ironviper/wiki/Journal).

Are you a photographer? I want to hear from you and learn what you need! DM @chrfrenning on Twitter or email me on christopher@frenning.com or give me a call at +41 (0) 76 518 08 77


## status all-up

Current status is that resource provisioning (setup.sh) is working, and manual uploads of files to 'file-store' container will result in thumbs and previews generated. a very simple web interface will display thumbnails and links to detail page.


## how to get started

1. You need an Azure subscription.
1. Fire up the [Azure Cloud Shell](https://shell.azure.com/) using Bash.
1. Issue the command below to build the infrastructure and start up the latest version of the app

```
    
    curl -sL https://raw.githubusercontent.com/chrfrenning/ironviper/main/setup.sh | bash 
    
```

1. Upload some files using 'python tools/upload.py' ([Alternative upload tools.](https://github.com/chrfrenning/ironviper/wiki/How-to-upload-files))
1. Inspect the files+folder tables for fileinfo and metadata, pv-store to see output
1. See url presented at end of setup for very naïve web ui

## what you get

If you're not diving into the tech itself, this is all you get at the moment:

<img src="https://github.com/chrfrenning/ironviper/raw/main/docs/gridview.jpg" width=400>


## plan


1. Complete the Proof of Concept stage. BTW: All plans moved to the [PoC project here in GitHub](https://github.com/chrfrenning/ironviper/projects/1).
2. Figure out if this is viable, and if so grind on, if not kill the project.

For more information, [see the roadmap](https://github.com/chrfrenning/ironviper/wiki/Roadmap).

## how to get involved

Things I need help with on this project:

1. I need to hear from photographers - enthustiasts and professionals alike to learn what you need and want
1. Contributors to the project - ideas, UX, frontend, backend, testing - just about anything. [See details on how to contribute here.](https://github.com/chrfrenning/ironviper/wiki/Contributing-to-this-project)
1. Consider [:coffee: donating coffee to keep me going ](https://www.buymeacoffee.com/chrfrenning).

## me

Made in ![Swiss Flag](https://chphno.blob.core.windows.net/ironviper-static/switzerland-flag-icon-16.png)+![Norwegian Flag](https://chphno.blob.core.windows.net/ironviper-static/norway-flag-icon-16.png) by a ![Norwegian Flag](https://chphno.blob.core.windows.net/ironviper-static/norway-flag-icon-16.png). Inspired by the light in alps and fjords + love of quality, chocolate and great food.
