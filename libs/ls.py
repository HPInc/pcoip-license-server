from requests.packages.urllib3.util import Retry
from requests.adapters import HTTPAdapter
from requests import Session, exceptions


def _handle_unauthorized(func):
    '''
    Re-authenticates and retries if 401 is received.
    '''
    def wrapper(*args, **kwargs):
        resp = func(*args, **kwargs)
        if resp.status_code == 401:
            client_instance = args[0]
            client_instance.authenticate()
            resp = func(*args, **kwargs)
        return resp
    return wrapper


class LSClient():
    '''
    Very simple interface around the rest API's. The https methods are decorated
    so that an expired authorization token will re-authenticate and retry the
    request. 

    TODO: Add error handling around Connection Errors
    '''

    def __init__(self, uri, username, password):
        if uri.startswith('http'):
            self.url = uri
            self.cls = '~'
        else:
            self.url = 'https://teradici.compliance.flexnetoperations.com'
            self.cls = uri
		
        self.creds = {
            "password": password,
            "user": username,
        }
        self._session = Session()
        self._session.mount(self.url, HTTPAdapter(
            max_retries=Retry(total=3, status_forcelist=[500, 503, 502]))
        )
        self.authenticate()

    @property
    def instances(self):
        return f"{self.url}/api/1.0/instances/{self.cls}/"

    @_handle_unauthorized
    def _get(self, url, token, data=dict(), **kwargs):
        return self._session.get(url=url,
                            headers=dict(authorization="Bearer " + self.token),
                            params=data)

    def authenticate(self):
        resp = self._session.post(
            url=f"{self.instances}/authorize", json=self.creds)

        if not resp.status_code == 200:
            msg = ("Authentication Error: Response code: {}. "
                "Please verify ls url or cls id, username and password and try again.".format(resp.status_code))
            raise Exception(msg)

        token = resp.json()["token"]
        self.token = token
        return token

    def get_instances(self):
        resp = self._get(
            url=f"{self.instances}", token=self.token)
        return resp.json()

    def get_features(self):
        resp = self._get(
            url=f"{self.instances}/features", token=self.token)
        return resp.json()

    def get_feature(self, feature_id):
        resp = self._get(
            url=f"{self.instances}/features/{feature_id}", token=self.token)
        return resp.json()

    def get_usage(self, feature_id):
        resp = self._get(
            url=f"{self.instances}/features/{feature_id}/clients", token=self.token)
        return resp.json()

    def get_reservation_groups(self):
        resp = self._get(
            url=f"{self.instances}/reservationgroups", token=self.token)
        return resp.json()

    def get_used_features(self):
        features = self.get_features()

        rd = {
            "standard": {
                "count": 0,
                "used": 0
            },
            "graphics": {
                "count": 0,
                "used": 0
            }
        }

        for item in features:
            if (item["featureName"] == "Agent-Session"):
                license_type = 'standard'
            elif (item["featureName"] == "Agent-Graphics"):
                license_type = 'graphics'

            rd[license_type]["count"] += item["featureCount"]
            rd[license_type]["used"] += item["used"]

        return rd
