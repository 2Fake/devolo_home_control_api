from json import JSONDecodeError

from requests.exceptions import ConnectTimeout, ReadTimeout


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.ok = not 400 <= self.status_code <= 600
        self.url = "https://homecontrol.mydevolo.com"


class MockResponseConnectTimeout(MockResponse):
    def get(self, url, auth=None, timeout=None):
        raise ConnectTimeout


class MockResponseGet(MockResponse):
    def get(self, url, auth=None, timeout=None):
        return MockResponseGet({"link": "test_link"}, status_code=200)

    def json(self):
        return self.json_data


class MockResponseJsonError(MockResponse):
    def get(self, url, auth=None, timeout=None):
        raise JSONDecodeError(msg="message", doc="doc", pos=1)


class MockResponsePost(MockResponse):
    def post(self, url, auth=None, timeout=None, headers=None, data=None):
        return MockResponsePost({"link": "test_link"}, status_code=200)

    def json(self):
        return {"id": 2}


class MockResponseReadTimeout(MockResponse):
    def post(self, url, auth=None, timeout=None, headers=None, data=None):
        raise ReadTimeout


class MockResponseServiceUnavailable(MockResponse):
    def get(self, url, auth=None, timeout=None):
        return MockResponseGet({"link": "test_link"}, status_code=503)

    def json(self):
        return self.json_data
