'''
.. copyright: Copyright 2020 Teradici Corporation

All Rights Reserved

No portions of this material may be reproduced in any form without the
written permission of Teradici Corporation.  All information contained
in this document is Teradici Corporation company private, proprietary,
and trade secret.
'''
import os
import requests
import time
from datetime import datetime
import argparse
from dotenv import load_dotenv
import json
import jsonstreams
load_dotenv()

from functools import partial

def ranged_integer(label, min_val, max_val, value):
    '''
    Simple validator for numeric (int) arguments. Provides the ability to
    specify min, max range and will raise more helpful exceptions if validation
    fails.
    '''
    try:
        value = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(
                "Provided {label} must be of numeric type".format(
                    label=label))

    msg = "Provided {label} of {value} must be smaller than {max} and greater than {min}".format(
            label=label, min=min_val, max=max_val, value=value)

    if value < min_val or value > max_val:
        raise argparse.ArgumentTypeError(msg)

    return int(value)

def environ_or_required(key):
    '''
    https://stackoverflow.com/questions/10551117/setting-options-from-environment-variables-when-using-argparse
    '''
    rv = (
            {'default': os.environ.get(key)} if os.environ.get(key)
            else {'required': True}
            )
    return rv

parser = argparse.ArgumentParser(description='''
This script displays the maximum CAS license concurrent usage over the Duration
period
''')

required = parser.add_argument_group("Required arguments")
required.add_argument("--lls-url", 
    help='''
Local License Server URL.
Example: http://10.0.1.1:7070

The value can be set from the environment variable: LLS_URL
''', **environ_or_required("LLS_URL"))

required.add_argument("--lls-username", 
    help='''
Local License Server Username. Used for acquiring an authorization token
while interacting with the REST API's.

The value for this can be set from the environment
variable: LLS_USERNAME
''', **environ_or_required("LLS_USERNAME"))

required.add_argument("--lls-password", 
    help='''
Local License Server Password. Used for acquiring an authorization token
while interacting with the REST API's.

The value for this can be set from the environment
variable: LLS_PASSWORD
''', **environ_or_required("LLS_PASSWORD"))

parser.add_argument("--duration", help=
        '''Periodically query license usage 
        over the defined duration in seconds. Defaults to 8 hours''', 
        action='store', required=False, default=8 * 60 * 60, 
        type=partial(ranged_integer, "duration", 60, 864000),
)

parser.add_argument("--delay", help=argparse.SUPPRESS,
        action='store', required=False, default=30,
        type=partial(ranged_integer, "duration", 60, 600),
        )

parser.add_argument("--alert-threshold", help=
        '''Percentage of used licenses available that will trigger an alert.''',
        action='store', required=False, default=15, 
        type=partial(ranged_integer, "duration", 0, 100)),

parser.add_argument("-o", "--output-file", help=
        '''Saves the results to a file.
        Currently the only supported format is json''',
        action='store', default=None)

def _handle_unathorized(func):
    '''
    Handles expired authentiction while interacting with the API"s
    '''
    def wrapper(*args, **kwargs):
        resp = func(*args, **kwargs)
        if resp.status_code == 401:
            client_instance = args[0]
            client_instance.authenticate()
            resp = func(*args, **kwargs)
        return resp
    return wrapper

class LLSClient():
    '''
    Very simple interface around the rest API's. The http methods are decorated
    so that an expired authorization token will re-authenticated and retry the
    request. 
    '''
    def __init__(self, url, username, password):
        self.url = url
        self.creds = {
            "password" : password,
            "user" : username,
        }
        self.authenticate()

    @_handle_unathorized
    def _get(self, url, token, data=dict(), **kwargs):
        return requests.get(url=url, 
                            headers=dict(authorization="Bearer " + self.token), 
                            params=data)

    def authenticate(self):
        resp=requests.post(url=self.url + "/api/1.0/instances/~/" + "authorize", json=self.creds)
        if not resp.status_code == 200:
            raise Exception(resp.text)

        token = resp.json()["token"]
        self.token = token
        return token

    def get_used_features(self):
        results = []
        resp = self._get(url=self.url + "/api/1.0/instances/~/features", token=self.token) 

        rd = {
            "standard" : {
                "count" : 0,
                "used"  : 0
            },
            "graphics" : {
                "count" : 0,
                "used"  : 0
            }
        }
        
        for item in resp.json(): 
            if (item["featureName"] == "Agent-Session"):
                rd["standard"]["count"] += item["featureCount"]
                rd["standard"]["used"] += item["used"]
            elif (item["featureName"] == "Agent-Graphics"):
                rd["graphics"]["count"] += item["featureCount"]
                rd["graphics"]["used"] += item["used"]    

        return rd

def display_as_table(list_of_lists, row_format=None):
    if not row_format:
        row_format = "{:>10}" * len(list_of_lists[0])

    for row in list_of_lists:
        print(row_format.format(*row))

def display_usage(client, iterations=5, delay=1, alert_threshold=15, outstream=None):
    header = ["Date", "Available - Standard Agent", "Max Used - Standard Agent", "Available - Graphics Agent", "Max Used - Graphics Agent", "Notes"]
    fmt = "{:>20}{:>30}{:>30}{:>30}{:>30}{:>60}"
    display_as_table([header], fmt)
    results = []

    for i in range(int(iterations), 0, -1):
        data = client.get_used_features()
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        note = ""

        for agent_type in ['graphics', 'standard']:
            count = data[agent_type]['count']
            if (count > 0) and (100 * data[agent_type]['used'] / count) >= alert_threshold:
                if note:
                    note += ","
                note += "{} threshold exceeded alert".format(agent_type)

        row = [now, 
            data['standard']['count'], 
            data['standard']['used'],
            data['graphics']['count'],
            data['graphics']['used'],
            note]

        if outstream:
            val = dict(
                available_standard_agent=data['standard']['count'],
                max_used_standard_agent=data['standard']['used'],
                available_graphics_agent=data['graphics']['count'],
                max_used_graphics_agent=data['graphics']['used'],
                note=note,
            )
            outstream.write(now, val)

        display_as_table([row], fmt)
        time.sleep(delay)

if __name__ == '__main__':
    args = parser.parse_args()

    client = LLSClient(args.lls_url, args.lls_username, args.lls_password)

    delay = args.delay
    duration = args.duration
    outfile = None
    iterations = round(duration / delay) or 1

    if args.output_file:
        with jsonstreams.Stream(jsonstreams.Type.object, filename=args.output_file) as outstream:
            display_usage(client,
                    iterations=iterations,
                    delay=delay,
                    alert_threshold=args.alert_threshold,
                    outstream=outstream,
            )
    else:
        display_usage(client,
                iterations=iterations,
                delay=delay,
                alert_threshold=args.alert_threshold,
        )
