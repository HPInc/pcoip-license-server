# python-pcoip-agent-lls
Tool that displays the maximum CAS license concurrent usage over time


## Setup Instructions

To install the dependency packages, run:

```
python3 -m pip install -r requirements.txt
```

## Usage

Create a filename named: ```.env``` in the checkout directory that contains the following:


```
LLS_URL=https://<address-of-lls>
LLS_USERNAME=<username>
LLS_PASSWORD=<password>
```

This information will be automatically used at startup. Alterntiavely, this
information can be provided as command line parameters --lls-url,
--lls-username, and --lls-password

