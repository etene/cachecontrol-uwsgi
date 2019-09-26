# cachecontrol-uwsgi
[![Build Status](https://travis-ci.org/etene/cachecontrol-uwsgi.svg?branch=master)](https://travis-ci.org/etene/cachecontrol-uwsgi) [![Coverage Status](https://coveralls.io/repos/github/etene/cachecontrol-uwsgi/badge.svg?branch=travis-ci)](https://coveralls.io/github/etene/cachecontrol-uwsgi?branch=travis-ci)

Backend for [CacheControl](https://github.com/ionrock/cachecontrol) using [uwsgi's caching framework](https://uwsgi-docs.readthedocs.io/en/latest/Caching.html).

Only works inside of uWSGI (the `uwsgi` module must be importable), and needs a configured cache (see uWSGI's `--cache2` option) to work.

For an example uWSGI setup with a working cache, see [test_app.py](./test_app.py) and [its integration tests](./tests/integration.py) inside the repository. It's a test application that doesn't use CacheControl but has a configured cache that works.

## Usage

```python
import requests

from cachecontrol import CacheControl
from cachecontrol_uwsgi import UWSGICache

cached_session = CacheControl(requests.session(), cache=UWSGICache("cache_name"))

response = cached_session.get("http://httpbin.org/status/200")
```
