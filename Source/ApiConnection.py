import sys
import requests
import logging
import urllib.parse


class ApiConnection(object):

    def __init__(self, tenant_id=None, client_key=None, secret_key=None, publisher_id=None, **kwargs):
        """
        Object that creates the authorization headers for- and sends API requests to the Microsoft Office APIs'.
        Taken from a Microsoft sample script that I cannot find the original of to reference.
        :param tenant_id: tenant ID of of Office/Azure subscription
        :param client_key: key (ID) of the application created in Azure to allow API access
        :param secret_key: key (secret) generated by the application created in Azure
        :param publisher_id: random GUID for API throttling; if none is given you are using public API limits and will probably be throttled (str)
        """
        self.tenant_id = tenant_id
        self.client_key = client_key
        self.secret_key = secret_key
        self.publisher_id = publisher_id
        self._headers = None

    @property
    def headers(self):
        """
        Generate headers once then return from cache.
        :return: authorization headers to use in https requests
        """
        if not self._headers:
            self._headers = self.login()
        return self._headers

    def login(self):
        """
        Login to get access token and cache it to make API requests with.
        :return: authorization headers (dict)
        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        auth_url = 'https://login.microsoftonline.com/{0}/oauth2/token'.format(self.tenant_id)
        resource = 'https://manage.office.com'
        data = 'grant_type=client_credentials&client_id={0}&client_secret={1}&resource={2}'.format(
            self.client_key, urllib.parse.quote(self.secret_key), resource)
        r = requests.post(auth_url, headers=headers, data=data, verify=True)
        resp = r.json()
        if not self.publisher_id:
            self.publisher_id = self.tenant_id
        try:
            headers['Authorization'] = 'bearer ' + resp['access_token']
            logging.log(level=logging.DEBUG, msg='Logged in')
            return headers
        except KeyError as e:
            logging.log(level=logging.ERROR, msg='Error logging in: "{0}"'.format(e))
            sys.exit(1)

    def make_api_request(self, url, append_url=True, get=True):
        """
        Make an API requests by appending the resource to the base URL. E.g. url='subscriptions/list'.
        Disable append_url to make the call to the literal passed URL.
        :param url: string
        :param append_url: bool
        :return: requests response
        """
        if append_url:
            url = 'https://manage.office.com/api/v1.0/{0}/activity/feed/{1}'.format(self.tenant_id, url)
        if self.publisher_id:
            url = '{0}{1}PublisherIdentifier={2}'.format(
                url,  '?' if '?' not in url.split('/')[-1] else '&', self.publisher_id if self.publisher_id else '')
        logging.log(level=logging.DEBUG, msg='Making API request using URL: "{0}"'.format(url))
        if get:
            status = requests.get(url, headers=self.headers, verify=True, timeout=120)
        else:
            status = requests.post(url, headers=self.headers, verify=True, timeout=120)
        return status


