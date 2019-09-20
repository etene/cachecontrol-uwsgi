from distutils.spawn import find_executable
from os import path
from shutil import rmtree
from subprocess import Popen
from tempfile import mkdtemp
from time import sleep
from datetime import datetime

import pytest
import requests_unixsocket

UWSGI = find_executable("uwsgi")

assert UWSGI is not None, "uwsgi executable not found !"


class UWSGIFixture:

    def __enter__(self):
        # Temp dir for app & stats sockets
        self.wd = mkdtemp("cachecontrol-uwsgi-test")
        # mapping of type to socket file for app & stats
        self.socks = {
             i: path.join(self.wd, "%s_sock" % i)
             for i in ("app", "stats")
        }
        # The cache name for uwsgi
        self.cache_name = "test_cache"
        # http over unix socket client
        self.session = requests_unixsocket.Session()
        self.uwsgi = Popen([
                UWSGI,
                "--http-socket", self.socks["app"],
                "--wsgi-file", "test_app.py",
                "--need-app",
                "--stats", self.socks["stats"],
                "--stats-http",
                "--cache2", "name=%s,items=10,bitmap=1" % self.cache_name,
                "--die-on-term",
                # "--master",
            ],
            env={"CACHE_NAME": self.cache_name}
        )
        # wait for sockets to be created by uwsgi
        for _ in range(10):
            if all(map(path.exists, self.socks.values())):
                break
            sleep(1)
        else:
            raise TimeoutError("uwsgi didn't start")
        return self

    def sock_url(self, name):
        """The request_unixsocket compatible url for a given sock type"""
        return "http+unix://" + self.socks[name].replace("/", "%2F")

    def assert_cache_state(self, **state):
        """Asserts the given items have the given value in the cache state"""
        resp = self.session.get(self.sock_url("stats"))
        resp.raise_for_status()
        caches = resp.json()["caches"]
        assert len(caches) == 1
        cache = caches[0]  # There's only one cache
        for key, value in state.items():
            assert cache[key] == value, \
                "Unexpected value for {}: {} != {}".format(
                    key, cache[key], value
                )

    def request(self, http_method, path, *args, **kwargs):
        """Make a request to the test app"""
        meth = getattr(self.session, http_method)
        url = self.sock_url("app") + path
        return meth(url, *args, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.uwsgi.terminate()
        self.uwsgi.wait()
        rmtree(self.wd, ignore_errors=True)


@pytest.fixture
def uwsgi_server():
    with UWSGIFixture() as server:
        yield server


def test_set_cache(uwsgi_server):
    cache_key = "/testkey"
    cache_content = b"hello"
    # cache is not set for now
    uwsgi_server.assert_cache_state(items=0)
    assert uwsgi_server.request("get", cache_key).status_code == 404

    # Set an entry
    assert uwsgi_server.request("post", cache_key, data=cache_content)
    # It's here
    uwsgi_server.assert_cache_state(items=1)
    # Retrieve it
    resp = uwsgi_server.request("get", cache_key)
    # Check its contents
    assert resp.content == cache_content


def test_delete_cache(uwsgi_server):
    # Create five cache entries
    entries = {"/key%d" % i: b"value%d" % i for i in range(5)}
    for key, value in entries.items():
        assert uwsgi_server.request("post", key, data=value)

    # Check they're all here
    uwsgi_server.assert_cache_state(items=5)

    # Delete one of them
    assert uwsgi_server.request("delete", "/key1")
    # There are now 4 items
    uwsgi_server.assert_cache_state(items=4)

    # Clear the cache
    assert uwsgi_server.request("delete", "/")
    # No items left
    uwsgi_server.assert_cache_state(items=0)


def test_cache_expiration(uwsgi_server):
    # Create an entry that expires in 2 seconds
    # (one second isn't enough, it gets rounded down)
    cache_key = "/expires_after_1s"
    cache_content = b"be gone"
    # expires = int(datetime.utcnow().timestamp()) + 2  # py3 only
    expires = int(datetime.utcnow().strftime("%s")) + 2
    assert uwsgi_server.request(
        "post", cache_key,
        data=cache_content, params={"expires": expires}
    )
    uwsgi_server.assert_cache_state(items=1)
    sleep(3)
    # cache entry is not set anymore
    uwsgi_server.assert_cache_state(items=0)


def test_update_cache(uwsgi_server):
    cache_key = "/testkey"
    cache_content = b"hello", b"world"
    # Set an entry
    resp = uwsgi_server.request("post", cache_key, data=cache_content[0])
    assert resp.ok
    uwsgi_server.assert_cache_state(items=1)
    # overwrite it
    resp = uwsgi_server.request("post", cache_key, data=cache_content[1])
    assert resp.ok
    uwsgi_server.assert_cache_state(items=1)
    resp = uwsgi_server.request("get", cache_key)
    assert resp.ok
    assert resp.content == cache_content[1]
