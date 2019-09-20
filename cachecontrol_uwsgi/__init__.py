from datetime import datetime

from cachecontrol.cache import BaseCache

import uwsgi


class UWSGICacheError(Exception):
    pass


class UWSGICache(BaseCache):
    def __init__(self, name=None):
        self.name = name

    def get(self, key):
        return uwsgi.cache_get(key, self.name)

    def set(self, key, value, expires=None):  # noqa: A003
        if expires:
            expires = int((expires - datetime.utcnow()).total_seconds())
            assert expires, "Cache entry expires too soon"
        else:
            # Undocumented: passing expire=0 means no expiration
            expires = 0
        # Undocumented: returns True on success, None otherwise
        # use cache_update because cache_set doesn't work for existing entries
        if not uwsgi.cache_update(key, value, expires, self.name):
            raise UWSGICacheError("Could not set %r in cache" % key)

    def delete(self, key):
        uwsgi.cache_del(key, self.name)

    def clear(self):
        uwsgi.cache_clear(self.name)

    def close(self):  # pragma nocover
        """not relevant for uwsgi"""
        pass
