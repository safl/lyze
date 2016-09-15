#!/usr/bin/env python3
"""
    lyze - liberate your zendesk entities

    As the name suggests, liberates your tickets, ticket_events, and other
    entities available via "incremental export" from the zendesk stronghold.
"""
import argparse
import json
import time
import requests

API_PREFIX = "/api/v2"
API_URI = "/incremental/%s.json?start_time=%d"
API_ENTITIES = ["tickets", "ticket_events", "organizations", "users"]

ERR_MSG = {
    429: """
******************************************************************************
You are being rate-limited, even though you are NOT violating rate limits.
Contact zendesk support and tell them that you are not a DDOS attack, you
just want your data.
******************************************************************************
"""
}

RATE = {
    "limit": 10,
    "remaining": 10,
    "start": None
}

def api_request(cred, resource):
    """Send a request to zendesk."""

    if not resource.startswith("http"):
        url = cred.url.rstrip('/')

        if not url.endswith(API_PREFIX):
            url += API_PREFIX

        url = "%s/%s" % (url, resource.lstrip('/'))

    user = "%s/token" % cred.user
    pswd = cred.token

    if not RATE["start"]:       # Super simple rate limiting
        RATE["start"] = time.time()

    if RATE["remaining"] == 1:
        time.sleep(60 - (RATE["start"] - time.time()))
        RATE["start"] = None
        RATE["remaining"] = RATE["limit"]

    response = requests.get(url, auth=(user, pswd))
    code = response.status_code

    RATE["remaining"] -= 1

    if code == 200:
        return response

    print("Request(%s) failed(%d) limit(%d/%d)" % (
        url, response.status_code, RATE["limit"], RATE["remaining"]
    ))

    if code in ERR_MSG:
        print(ERR_MSG[code])

    return None

class Cred(object):
    """Represents zendesk credentials."""

    def __init__(self, url, user, token):
        self.url = url
        self.user = user
        self.token = token

    @classmethod
    def from_dict(cls, dct):
        """Construct cred from dictionary."""

        return cls(dct["url"], dct["user"], dct["token"])

    @classmethod
    def from_json(cls, path):
        """Construct cred from json file."""

        with open(path, "r") as json_fd:
            cred = json.load(json_fd)

        return cls.from_dict(cred)

    def to_dict(self):
        """Represent Cred as dictionary."""

        return {
            "url": self.url,
            "user": self.user,
            "token": self.token,
        }

    def __repr__(self):
        """Textual representation of Cred."""

        return self.to_dict()

def cmd_liberate(args):
    """Liberate an entity from zendesk."""

    cred = Cred.from_json(args.cred)
    entities = API_ENTITIES if args.entity == "ALL" else [args.entity]

    for entity in entities:
        start_time = int(args.start_time)
        excess = 2
        while excess:
            resource = API_URI % (entity, start_time)
            response = api_request(cred, resource)

            if not response:
                print("Stopping: due to request error")
                break

            tickets = response.json()

            end_time = int(tickets["end_time"])

            fname = "%s_%010d_%010d.json" % (entity, start_time, end_time)
            with open(fname, 'w') as fjson:
                json.dump(tickets, fjson, indent=4)

            print("Liberated '%s': %s" % (entity, fname))

            if start_time == end_time:
                excess -= 1
                print("Stopping: about to... going %d time(s) more..." % excess)

            start_time = end_time

def cmd_check(cred):
    """Check credentials."""

    cred = Cred.from_json(args.cred)

    if api_request(cred, "/incremental/users/sample.json?start_time=0"):
        print("Credentials seem valid, enjoy.")

def main():
    """
    Main entry-point, parses command-line arguments and delegates execution
    to cli command handling function, cmd_*
    """

    p_main = argparse.ArgumentParser(description="Liberate your zendesk data")
    p_main.add_argument(
        "--cred",
        dest="cred",
        type=str,
        default="lyze.cred",
        help='Path to credentials file'
    )

    p_subs = p_main.add_subparsers()

    p_liberate = p_subs.add_parser("liberate")
    p_liberate.add_argument(
        "--entity",
        dest="entity",
        type=str,
        default="ALL",
        choices=["ALL"] + API_ENTITIES,
        help="Entity to liberate"
    )
    p_liberate.add_argument(
        "--start_time",
        dest="start_time",
        type=int,
        default=0,
        help="Start time of liberation"
    )
    p_liberate.set_defaults(func=cmd_liberate)

    p_check = p_subs.add_parser("check")
    p_check.set_defaults(func=cmd_check)

    args = p_main.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
