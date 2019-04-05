from f0cal.bootstrap.helpers import UrlTokens


def _get_test(tokens, attr, value):
    assert getattr(tokens, attr) == value


def test_get():
    _all = [
        ("https://github.com/f0cal/manifest.git", dict(username=None, password=None)),
        (
            "https://foo@github.com/f0cal/manifest.git",
            dict(username="foo", password=None),
        ),
        (
            "https://foo:bar@github.com/f0cal/manifest.git",
            dict(username="foo", password="bar"),
        ),
    ]
    for pre, attrs in _all:
        tokens = UrlTokens.from_str(pre)
        for attr, value in attrs.items():
            yield _get_test, tokens, attr, value


def _set_test(tokens, attr, value):
    setattr(tokens, attr, value)
    assert getattr(tokens, attr) == value


def test_set():
    _all = [
        ("https://github.com/f0cal/manifest.git", dict(username="foo")),
        ("https://github.com/f0cal/manifest.git", dict(username="foo", password="bar")),
    ]
    for pre, attrs in _all:
        tokens = UrlTokens.from_str(pre)
        for attr, value in attrs.items():
            yield _set_test, tokens, attr, value


def _update_test(pre, kwargs, post):
    assert UrlTokens.update_url(pre, **kwargs) == post


def test_update():
    _all = [
        (
            "https://github.com/f0cal/manifest.git",
            dict(username="foo", password="bar"),
            "https://foo:bar@github.com/f0cal/manifest.git",
        )
    ]
    for pre, kwargs, post in _all:
        yield _update_test, pre, kwargs, post
