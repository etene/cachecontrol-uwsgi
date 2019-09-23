import sys
from datetime import datetime, timedelta
from mock import Mock, patch
import pytest
from cachecontrol import CacheControl
from requests import Session
import responses
from collections import defaultdict

TIME_FMT = "%a, %d %b %Y %H:%M:%S GMT"


@pytest.fixture(scope="function", params=("testcache", None))
def cachecontrol_uwsgi(request):
    with patch.dict(sys.modules, {"uwsgi": Mock()}):

        # Configure mocked uwsgi
        import cachecontrol_uwsgi as mod
        fake_cache = defaultdict(dict)

        def fake_cache_update(key, value, expire=0, name=None):
            fake_cache[name][key] = value
            return True

        def fake_cache_get(key, name=None):
            return fake_cache[name].get(key)

        mod.uwsgi.cache_update.side_effect = fake_cache_update
        mod.uwsgi.cache_get.side_effect = fake_cache_get

        yield mod.UWSGICache(request.param), mod.uwsgi


def test_bare(cachecontrol_uwsgi):
    """Run tests without CacheControl"""
    cache, uwsgi = cachecontrol_uwsgi
    # Set
    cache.set("key", "value")
    uwsgi.cache_update.assert_called_once_with("key", "value", 0, cache.name)
    # Get
    cache.get("key")
    uwsgi.cache_get.assert_called_once_with("key", cache.name)
    # Delete
    cache.delete("key")
    uwsgi.cache_del.assert_called_once_with("key", cache.name)
    # Clear
    cache.clear()
    uwsgi.cache_clear.assert_called_once_with(cache.name)
    # Expire
    expires = datetime.utcnow() + timedelta(seconds=10)
    expected_expire_arg = 9  # Rounded down
    uwsgi.cache_update.reset_mock()
    cache.set("expiring_key", "expiring_value", expires)
    uwsgi.cache_update.assert_called_once_with(
        "expiring_key", "expiring_value", expected_expire_arg, cache.name
    )


@responses.activate
def test_with_cachecontrol(cachecontrol_uwsgi):
    """Run tests with CacheControl"""
    cache, mocked_uwsgi = cachecontrol_uwsgi
    cached_session = CacheControl(Session(), cache)

    # Configure fake responses
    url = "http://host/api"
    contents = {'hello': 'world'}
    responses.add(
        method=responses.GET,
        url=url,
        json=contents,
        status=301,  # 301 requests are cached unconditionally
    )
    responses.add(
        method=responses.DELETE,
        url=url,
        status=204,
    )

    # First call: this will cache the response because it isn't in the cache
    cached_session.get(url)
    assert len(responses.calls) == 1
    assert responses.calls[-1].request.method == responses.GET
    mocked_uwsgi.cache_get.assert_called_with(url, cache.name)
    mocked_uwsgi.cache_update.assert_called_once()

    # The response should have been cached
    cached_session.get(url)
    assert len(responses.calls) == 1
    mocked_uwsgi.cache_get.assert_called_with(url, cache.name)
    mocked_uwsgi.cache_update.assert_called_once()

    # The cache should be invalidated & deleted
    cached_session.delete(url)
    assert len(responses.calls) == 2
    assert responses.calls[-1].request.method == responses.DELETE
    mocked_uwsgi.cache_del.assert_called_with(url, cache.name)
