from functools import partial
import os
from os.path import abspath, join, dirname
import time
from datetime import datetime
import argparse
from dotenv import load_dotenv
import json
import sys
import jsonstreams
import re
sys.path.append(dirname(abspath(dirname(__file__))))

from libs.ls import LSClient

load_dotenv()

MIN_THRESHOLD_PERCENT = 0
DEFAULT_THRESHOLD_PERCENT = 80
MAX_THRESHOLD_PERCENT = 100

MIN_DELAY_MINUTES = 1
DEFAULT_DELAY_MINUTES = 1
MAX_DELAY_MINUTES = 5

MIN_DURATION_MINUTES = 1
DEFAULT_DURATION_MINUTES = 8 * 60
MAX_DURATION_MINUTES = 10 * 24 * 60


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

def validate_ls_endpoint(value):
    '''
    Simple validator for ls url against http or https. Warning is issued if
    using http.
    '''
    if not value.startswith('http://') and not value.startswith('https://'):
        return validate_cls_id(value)

    if value.startswith('http://'):
        msg = '''
\n
\t\tTeradici highly recommends setting up the Local License Server as an HTTPS 
\t\tserver otherwise the username and password are transmitted in clear text
\n
'''
        print(msg)

    return value
	
def validate_cls_id(value):
    '''
    Simple validator for cls-id.
    '''
    if re.match("^[0-9A-Z]{12}$", value) is None:
        msg = "Cloud License Service ID must be 12 characters long and only include 0-9,A-Z"
        raise argparse.ArgumentTypeError(msg)
    return value

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
This script displays the maximum Cloud Access Software license concurrent usage over the Duration
period
''')


required = parser.add_argument_group("Required arguments")

required.add_argument("--ls-uri",
                      help='''
Local License Server URL
(Example: https://10.0.1.1:7071)

or Cloud License Service ID
(Example: 1EJD8DXUKQWQ).

The value can be set from the environment variable: LLS_URI
''', **environ_or_required("LS_URI"), type=validate_ls_endpoint)

required.add_argument("--ls-username",
                      help='''
License Server Username. This is likely 'admin'.

The value for this can be set from the environment
variable: LS_USERNAME
''', **environ_or_required("LS_USERNAME"))

required.add_argument("--ls-password",
                      help='''
License Server Password. 

The value for this can be set from the environment
variable: LS_PASSWORD
''', **environ_or_required("LS_PASSWORD"))

parser.add_argument("--duration", help='''Periodically query license usage 
        over the defined duration (in minutes) and output the results.
        Defaults to 4 hours. (min 120 seconds).
        ''',
                    action='store', required=False, default=DEFAULT_DURATION_MINUTES,
                    type=partial(ranged_integer, "duration", MIN_DURATION_MINUTES, MAX_DURATION_MINUTES),
                    )

parser.add_argument("--delay", help=argparse.SUPPRESS,
                    action='store', required=False, default=DEFAULT_DELAY_MINUTES,
                    type=partial(ranged_integer, "duration", MIN_DELAY_MINUTES, MAX_DELAY_MINUTES),
                    )

parser.add_argument("--alert-threshold",
        help='''Percentage from 0-100 of used licenses available that will trigger an alert.''',
                    action='store', required=False, default=DEFAULT_THRESHOLD_PERCENT,
                    type=partial(ranged_integer, "duration", MIN_THRESHOLD_PERCENT, MAX_THRESHOLD_PERCENT)),

parser.add_argument("-o", "--output-file", help='''Saves the results to a file.
        Currently the only supported format is json''',
                    action='store', default=None)


def display_as_table(list_of_lists, row_format=None):
    if not row_format:
        row_format = "{:>10}" * len(list_of_lists[0])

    for row in list_of_lists:
        print(row_format.format(*row))


def display_usage(client, iterations=5, delay=1, alert_threshold=15, outstream=None):
    header = ["Date", "Total - Standard Agent", "Max Used - Standard Agent",
              "Total - Graphics Agent", "Max Used - Graphics Agent", "Notes"]
    fmt = "{:>20}{:>30}{:>30}{:>30}{:>30}{:>50}"
    display_as_table([header], fmt)
    _first_iteration = True

    while True:
        results = []
        note = ""

        for _ in range(int(iterations), 0, -1):
            data = client.get_used_features()
            results.append(data)
            if _first_iteration:
                _first_iteration = False
                break
            time.sleep(delay)

        # compute the max usage counts over the duration.
        standard_total = max([row['standard']['count'] for row in results])
        standard_used = max([row['standard']['used'] for row in results])
        graphics_total = max([row['graphics']['count'] for row in results])
        graphics_used = max([row['graphics']['used'] for row in results])

        data = dict(
            available_standard_agent=standard_total,
            max_used_standard_agent=standard_used,
            available_graphics_agent=graphics_total,
            max_used_graphics_agent=graphics_used,
        )

        for agent_type, count, used in [
                ('standard', standard_total, standard_used),
                ('graphics', graphics_total, graphics_used)]:
            if (count > 0) and (100 * used / count) >= alert_threshold:
                if note:
                    note += ","
                note += "{} threshold alert".format(agent_type)

        data['note'] = note

        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        if outstream:
            outstream.write(now, data)

        display_as_table(
                [[
                    now,
                    data['available_standard_agent'], data['max_used_standard_agent'],
                    data['available_graphics_agent'], data['max_used_graphics_agent'],
                    data['note'],
                ]], fmt
        )


if __name__ == '__main__':
    args = parser.parse_args()
    uri = args.ls_uri

    client = LSClient(uri, args.ls_username, args.ls_password)

    msg = "\t\tOutput will appear on the console every {} minute".format(
            args.duration)

    if args.duration > 1:
        msg += "s"

    print(msg, '\n\n')


    # convert the provided arguments from minutes to seconds
    delay = args.delay * 60
    duration = args.duration * 60
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
