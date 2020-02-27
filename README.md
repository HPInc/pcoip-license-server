# python-pcoip-agent-lls

| DISCLAIMER |
| --- |
| This script is provided as-is and is not supported by Teradici. It is intended to provide a reference for accessing the Local License Server APIs. Please report any issues via github. |


Tool that displays the maximum Cloud Access Software license concurrent usage over time.
Once the tool is started, it will continue to run and output results until terminated.


## Setup Instructions

To install the dependency packages, run:

```
python3 -m pip install -r requirements.txt
```

## Usage

Create a filename named: ```.env``` in the checkout directory that contains the following:


```
LLS_URL=https://<address-of-lls>:<port>
LLS_USERNAME=<username>
LLS_PASSWORD=<password>
```

This information will be automatically used at startup. Alterntiavely, this
information can be provided as command line parameters --lls-url,
--lls-username, and --lls-password

```
usage: pcoip-agent-lls.py [-h] [--lls-url LLS_URL]
                          [--lls-username LLS_USERNAME]
                          [--lls-password LLS_PASSWORD] [--duration DURATION]
                          [--alert-threshold ALERT_THRESHOLD] [-o OUTPUT_FILE]

This script displays the maximum CAS license concurrent usage over the
Duration period

optional arguments:
  -h, --help            show this help message and exit
  --duration DURATION   Periodically query license usage over the defined
                        duration (seconds) and output the results. Defaults to
                        4 hours. (min 120 seconds).
  --alert-threshold ALERT_THRESHOLD
                        Percentage from 0-100 of used licenses available that
                        will trigger an alert. Defaults to 80.
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Saves the results to a file. Currently the only
                        supported format is json

Required arguments:
  --lls-url LLS_URL     Local License Server URL. Example:
                        http://10.0.1.1:7070 The value can be set from the
                        environment variable: LLS_URL
  --lls-username LLS_USERNAME
                        Local License Server Username. Used for acquiring an
                        authorization token while interacting with the REST
                        API's. The value for this can be set from the
                        environment variable: LLS_USERNAME
  --lls-password LLS_PASSWORD
                        Local License Server Password. Used for acquiring an
                        authorization token while interacting with the REST
                        API's. The value for this can be set from the
                        environment variable: LLS_PASSWORD
```

A warning will be printed if using http:// to communicate with LLS. Teradici
highly recommends communicating over secure connections. See License Server
Administration Guide "How to enable HTTPS/TLS for PCoIP License Server" at
https://help.teradici.com.

This script takes advantage of the LLS REST APIs documented at
```http://<address-of-lls>:<port>/documentation/swagger-ui.html```
