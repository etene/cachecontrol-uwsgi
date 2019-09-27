"""A cache provider for CacheControl using UWSGI's caching framework."""

import setuptools

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except IOError:
    long_description = (
        "A cache provider for "
        "[CacheControl](https://cachecontrol.readthedocs.io/) "
        "using UWSGI's caching framework."
    )

setuptools.setup(
    name="cachecontrol-uwsgi",
    version="1.0.0",
    author="etene",
    author_email="etienne.noss+pypi@gmail.com",
    description=__doc__,
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/etene/cachecontrol-uwsgi",
    packages=["cachecontrol_uwsgi"],
    install_requires=["cachecontrol"],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
)
