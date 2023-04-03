import io
import urllib, base64
from typing import Protocol

class TextStreamProvider(Protocol):
    def get_stream(self) -> io.TextIOWrapper:
        ...

class LocalTextStream:
    def __init__(self, path):
        self.path = path

    def get_stream(self) -> io.TextIOWrapper:
        return open(self.path, "rt")


class UrlTextStream:
    def __init__(self, url, username=None, password=None) -> None:
        self.ulr = url
        self.username = None
        self.password = None

    def get_stream(self) -> io.TextIOWrapper:
        request = urllib.request(self.url)
        if self.username and self.password:
            base64string = base64.b64encode('%s:%s' % (self.username, self.password))
            request.add_header("Authorization", "Basic %s" % base64string)   
        return request.urlopen(request)


class S3TextStream:
    def __init__(self, url, credentials) -> None:
        self.ulr = url
        self.credentials = credentials

    def get_stream(self) -> io.StringIO:
        return io.TextIOWrapper('todo')