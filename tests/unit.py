import sys
from unittest.mock import Mock, patch

import pytest


@pytest.fixture(scope="function", params=("testcache", None))
def cachecontrol_uwsgi(request):
    with patch.dict(sys.modules, {"uwsgi": Mock()}):
        import cachecontrol_uwsgi as mod
        yield mod.UWSGICache(request.param), mod.uwsgi


def test_set_cache(cachecontrol_uwsgi):
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
