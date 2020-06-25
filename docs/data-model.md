# Data Model

### Goals

* Source independent. Files can be 1) ingested to a centralized repository or 2) linked from other sources, e.g. Dropbox, Onedrive
* Quick lookup of independent files. Compound, random key for individual lookup. Consider filename metadata.
* Provide a tree structure to navigate assets
* Use materialized view for fast, highly scalable reader access. Prioritize massive read scale in design decisions. Use storage over compute.
* Opinionated and tactical on metadata for feature support and to maintain reasonably sized search indexes



### Individual lookup

Use compbound key: key = (hash(unique_id)%10000) '-' (shortform(unique_id))



### Materialized views

* Id lookup
* Checksum lookup

* Thumbs and previews
* Individual file information in detailed format (json) to support detail view rendering
* Tree structure (folders) with brief format (json) to support overview rendering
* Tag structure, brief format (json) to support overview rendering



### Duplication detection

Goal: help identify duplicates, goal of cleaning archive and saving storage cost

* Interactive ingestion: Warn and help with managing duplicate uploads
* Mass ingestion: Help identify and clean duplicates post-ingestion

 
### Comments

* Allow hiding 'trash' keywords, dictionary lookup in ingestion phase?
