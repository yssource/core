import github3
import datetime
import getpass
import urllib.parse


class GithubAPI(object):
    SCOPES = ("repo",)
    NOTE_URL = "http://f0cal.com"
    NOTE = "F0CAL boostrap -- {stamp}"

    def __init__(self, username=None, password=None):
        self._username = username
        self._password = password

    def get_auth(self):
        username = self.username
        password = self.password
        stamp = datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f%Z"
        )
        note = self.NOTE.format(stamp=stamp)
        print(username, password)
        auth = github3.authorize(username, password, self.SCOPES, note, self.NOTE_URL)
        return auth

    @property
    def username(self):
        if self._username is None:
            self._username = input("Github username: ")
        return self._username

    @property
    def password(self):
        if self._password is None:
            self._password = getpass.getpass("Github password: ")
        return self._password


# class UrlTokens(object):
#     _NETLOC = "{username}{psep}{password}{usep}{hostname}{hsep}{port}"
#     _EMPTY = ""

#     def __init__(self, parse_result):
#         self._parser_result = parse_result

#     @property
#     def username(self):
#         return self._parser_result.username

#     @username.setter
#     def username(self, value):
#         self._update_netloc(username=value)

#     @property
#     def password(self):
#         return self._parser_result.password

#     @password.setter
#     def password(self, value):
#         self._update_netloc(password=value)

#     @property
#     def hostname(self):
#         return self._parser_result.hostname

#     @property
#     def port(self):
#         return self._parser_result.port

#     def _update_netloc(self, username=None, password=None, hostname=None, port=None):
#         username = username or self.username or self._EMPTY
#         password = password or self.password or self._EMPTY
#         hostname = hostname or self.hostname or self._EMPTY
#         port = port or self.port or self._EMPTY
#         assert any([username, password, hostname, port])
#         usep = ""
#         if username or password:
#             usep = "@"
#         psep = ""
#         if username and password:
#             psep = ":"
#         hsep = ""
#         if port:
#             hsep = ":"
#         kwargs = dict(username=username, password=password, hostname=hostname,
#                       port=port, usep=usep, psep=psep, hsep=hsep)
#         netloc = self._NETLOC.format(**kwargs)
#         self._replace(netloc=netloc)

#     def _replace(self, **kwargs):
#         self._parser_result = self._parser_result._replace(**kwargs)

#     def to_str(self):
#         return urllib.parse.urlunparse(self._parser_result)

#     @classmethod
#     def from_str(cls, url):
#         return cls(urllib.parse.urlparse(url))

#     @classmethod
#     def update_url(cls, url, **dargs):
#         url_tokens = cls.from_str(url)
#         for key, value in dargs.items():
#             setattr(url_tokens, key, value)
#         return url_tokens.to_str()
