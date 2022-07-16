# API for IronViper


## Tree and Graph JSON API

Working on tree structure JSON API and file upload.

Next step is building the graph using metadata, tags, and ai enrichment from cognitive services.

* keywords/tags
* dates - years, months
* people - need a field to store people in xmp
* places - with geolookup, stop at country level?
* camera model, lens, focal length, aperture, exposure time, ISO, etc. - what is needed here?
* object recognition - faces, people, animals, which other?


## Test Uploads with Curl

get token:
curl -X GET /services/initialize-upload?path=/&filename=<filename.ext>
curl -X PUT -T <FILENAME.JPG> -H "x-ms-version: 2019-12-12" -H "x-ms-blob-type: BlockBlob" "<SASURLHERE>"