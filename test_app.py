from datetime import datetime
from os import getenv

from flask import Flask, Response, request

from cachecontrol_uwsgi import UWSGICache

cache = UWSGICache(getenv("CACHE_NAME"))

application = Flask(__name__)


@application.route("/<key>", methods=["GET", "POST", "DELETE"])
def cache_action(key):
    if request.method == "GET":
        return cache.get(key) or Response(status=404)
    elif request.method == "POST":
        expires = datetime.fromtimestamp(int(request.args.get("expires", 0)))
        cache.set(key, request.data or "", expires)
    elif request.method == "DELETE":
        cache.delete(key)
    return Response(status=200)


@application.route("/", methods=["DELETE"])
def cache_clear():
    cache.clear()
    return Response(status=200)
