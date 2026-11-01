# Source data is supplied, not committed

The invoice data, Vendor Master and procurement policy are not committed to this public repository. Reviewers already have the pack, and the data shouldn't be published. The backend reads them from `DATA_DIR` (default `./data`). If any expected file is missing at startup, it stops and names both the missing files and the path it searched. Without this, a reader would expect the app to run straight after cloning and might "fix" the ignore rule. The ECB rate snapshot is public data, so it is committed under `backend/`.
