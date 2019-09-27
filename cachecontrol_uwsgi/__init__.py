from datetime import datetime

from cachecontrol.cache import BaseCache

import uwsgi


class UWSGICacheError(Exception):
    """A call to the uWSGI cache API failed."""
    pass


class UWSGICache(BaseCache):
    def __init__(self, name=None, raise_on_errors=True):
        """Create a new UWSGICache instance.

        name:
            The cache name as configured in uwsgi.
        raise_on_errors:
            Determines whether an `UWSGICacheError` is raised
            when a call to the uwsgi cache API fails.
        """
        self.name = name
        self.raise_on_errors = raise_on_errors

    def _check_call(self, func, *args):
        """Call an uwsgi cache function & check its return status.

        These return `True` on success, `None` otherwise (undocumented ?).
        If the call fails and `raise_on_errors` is `True`,
        raises UWSGICacheError.
        """
        if func(*args) is None and self.raise_on_errors is True:
            raise UWSGICacheError(
                "Call to {name}({args}) failed".format(
                    name=func.__name__,
                    args=", ".join(map(repr, args))
                )
            )

    def get(self, key):
        """Gets an entry in the cache, returning `None` if it isn't set"""
        return uwsgi.cache_get(key, self.name)

    def set(self, key, value, expires=None):  # noqa: A003
        """Sets an entry in the cache.

        Raises a `ValueError` if `expires` is too soon.
        """
        if expires:
            expires = int((expires - datetime.utcnow()).total_seconds())
            if expires <= 0:
                raise ValueError("Cache entry expires too soon (in {} seconds)"
                                 .format(expires))
        else:
            # Undocumented: passing expire=0 means no expiration
            expires = 0
        # use cache_update because cache_set doesn't work for existing entries
        self._check_call(uwsgi.cache_update, key, value, expires, self.name)

    def delete(self, key):
        """Deletes a cache entry"""
        self._check_call(uwsgi.cache_del, key, self.name)

    def clear(self):
        """Deletes all cache entries"""
        self._check_call(uwsgi.cache_clear, self.name)

    def close(self):  # pragma nocover
        """not relevant for uwsgi"""
        pass
