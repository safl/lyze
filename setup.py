#!/usr/bin/env python
"""
    lyze - liberate your zendesk entities

    As the name suggests, liberates your tickets, ticket_events, and other
    entities available via "incremental export" from the zendesk stronghold.
"""
from distutils.core import setup

from lyze import APP_NAME, APP_VERS, APP_AUTH, APP_MAIL, APP_URL, APP_LICENSE
from lyze import APP_DESC

setup(
    name=APP_NAME.capitalize(),
    version=APP_VERS,
    author=APP_AUTH,
    author_email=APP_MAIL,
    description=APP_DESC,
    url=APP_URL,
    license=APP_LICENSE,
    scripts=["lyze.py"]
)
