# pcoip-agent-ls

| DISCLAIMER |
| --- |
| This script is provided as-is and is not supported by Teradici. It is intended to provide a reference for accessing the License Server (LS) or Cloud License Service (CLS) APIs. Please report any issues via github. |


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
LS_URL=https://<address-of-ls>:<port> OR CLS_ID=<your-cls-id>
LS_USERNAME=<username>
LS_PASSWORD=<password>
```

This information will be automatically used at startup. Alternatively, this
information can be provided as command line parameters --ls-url or --cls-id,
--ls-username, and --ls-password

```
usage: pcoip-agent-ls.py [-h] [--ls-url LS_URL | --cls-id CLS_ID]
                         --ls-username LS_USERNAME --ls-password LS_PASSWORD
                         [--duration DURATION]
                         [--alert-threshold ALERT_THRESHOLD] [-o OUTPUT_FILE]

This script displays the maximum CAS license concurrent usage over the
Duration period

optional arguments:
  -h, --help            show this help message and exit
  --ls-url LS_URL       Local License Server URL. Example:
                        https://10.0.1.1:7071 The value can be set from the
                        environment variable: LLS_URL (1)
  --cls-id CLS_ID       Cloud License Service ID. Example: 1EJD8DXUKQWQ The
                        value can be set from the environment variable: CLS_ID
                        (2)
  --duration DURATION   Periodically query license usage over the defined
                        duration (in minutes) and output the results. Defaults
                        to 4 hours. (min 120 seconds).
  --alert-threshold ALERT_THRESHOLD
                        Percentage from 0-100 of used licenses available that
                        will trigger an alert.
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Saves the results to a file. Currently the only
                        supported format is json

Required arguments:
  --ls-username LS_USERNAME
                        License Server Username. Used for acquiring an
                        authorization token while interacting with the REST
                        API's. This is likely 'admin'. The value for this can
                        be set from the environment variable: LS_USERNAME
  --ls-password LS_PASSWORD
                        License Server Password. Used for acquiring an
                        authorization token while interacting with the REST
                        API's. The value for this can be set from the
                        environment variable: LS_PASSWORD (3) (4)
```

(1) A warning will be printed if using http:// to communicate with Local License Server. Teradici
highly recommends communicating over secure connections (https://). See License Server
Administration Guide "How to enable HTTPS/TLS for PCoIP License Server" at
https://help.teradici.com.

(2) To get your CLS-ID, this is the first part (left of the @) in the Registration Code
you received from Teradici. For example, if the Registration Code is
XXXXXXX@YYYY-YYYY-YYYY-YYYY, the CLS-ID will be XXXXXXX.

(3) To set your CLS-ID password, do the following:
1. Log into https://teradici.flexnetoperations.com. To request access, create a case with
[Teradici support](https://help.teradici.com/s/contactsupport). Be prepared to provide a valid
Registration Code, and the name and email address of a contact person who should have access.
2. Go to "Served Licenses" -> "License Server" -> \<your CLS ID\> -> "Set Password".

(4) The LLS password is the same password used when the LLS was initially setup.


This script takes advantage of the LLS REST APIs documented at
```https://<address-of-ls>:<port>/documentation```
