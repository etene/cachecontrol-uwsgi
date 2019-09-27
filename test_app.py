from datetime import datetime
from os import getenv

from flask import Flask, Response, request

from cachecontrol_uwsgi import UWSGICache, UWSGICacheError

cache = UWSGICache(getenv("CACHE_NAME"))

application = Flask(__name__)


@application.route("/<key>", methods=["GET", "POST", "DELETE"])
def cache_action(key):
    try:
        if request.method == "GET":
            # GET /key -> return corresponding entry
            value = cache.get(key)
            if value is None:
                return Response(status=404)
            else:
                return value
        elif request.method == "POST":
            # POST /key -> store request data
            try:
                expires_stamp = int(request.args["expires"])
            except KeyError:
                # No expires parameter passed
                expires = None
            except ValueError as err:
                # Invalid parameter
                return Response(str(err), status=400)
            else:
                expires = datetime.fromtimestamp(expires_stamp)
            cache.set(key, request.data or "", expires)
        elif request.method == "DELETE":
            # DELETE /key -> delete corresponding entry
            cache.delete(key)
    except UWSGICacheError as err:
        # Raised if trying to delete an inexistent entry,
        # or if cache is full
        return Response(str(err), status=400)
    return Response(status=200)


@application.route("/", methods=["DELETE"])
def cache_clear():
    cache.clear()
    return Response(status=200)
