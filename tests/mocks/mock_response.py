from json import JSONDecodeError

from httpx import URL, ConnectTimeout, ReadTimeout


class MockResponse:

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.url = URL("http://test.test")


class MockResponseConnectTimeout(MockResponse):

    def get(self, url, auth=None, timeout=None):
        raise ConnectTimeout("", request=self)


class MockResponseGet(MockResponse):

    def get(self, url, auth=None, timeout=None):
        return MockResponseGet({"link": "test_link"},
                               status_code=200)

    def json(self):
        return self.json_data


class MockResponseJsonError(MockResponse):

    def get(self, url, auth=None, timeout=None):
        raise JSONDecodeError(msg="message", doc="doc", pos=1)


class MockResponsePost(MockResponse):

    def post(self, url, auth=None, timeout=None, headers=None, json=None):
        return MockResponsePost({"link": "test_link"},
                                status_code=200)

    def json(self):
        return {
            "id": 2
        }


class MockResponseReadTimeout(MockResponse):

    def post(self, url, auth=None, timeout=None, headers=None, json=None):
        raise ReadTimeout("", request=self)


class MockResponseServiceUnavailable(MockResponse):

    def get(self, url, auth=None, timeout=None):
        return MockResponseGet({"link": "test_link"},
                               status_code=503)

    def json(self):
        return self.json_data
