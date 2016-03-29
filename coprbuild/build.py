from __future__ import print_function, unicode_literals

import argparse
import json
import os
import requests

from functools import wraps
from psys import Error
from urlparse import urljoin

from . import config


SRPM_MIME_TYPE = "application/x-rpm"
"""MIME type for SRPM file."""

COPR_ENDPOINT = None
"""COPR service endpoint."""


def get_endpoint():
    """Returns COPR endpoint."""

    global COPR_ENDPOINT

    if not COPR_ENDPOINT:
        COPR_ENDPOINT = config.get("copr_url")
        response = requests.head(COPR_ENDPOINT)
        if response.is_redirect:
            COPR_ENDPOINT = response.headers["location"]

    return COPR_ENDPOINT


def _get_project_and_owner(name):
    """Returns parsed project line."""

    if "/" in name:
        return name.split("/")
    else:
        return config.get("username"), name


def get_project_id(name):
    """Returns project id by specified project name."""

    path = urljoin(get_endpoint(), "/api_2/projects")
    owner, project_name = _get_project_and_owner(name)
    if owner:
        path += "?owner={0}".format(owner)

    response = requests.get(path)
    response.raise_for_status()
    response = json.loads(response.text)

    projects_map = dict([(project["project"]["name"], project["project"])
                        for project in response["projects"]])

    if project_name not in projects_map:
        raise Error("COPR project '{0}' not found.", name)

    return projects_map[project_name]["id"]


def build(project, srpm):
    """Builds specified SRPM."""

    srpm_path = os.path.abspath(os.path.expanduser(srpm))
    if not os.path.exists(srpm_path):
        raise Error("SRPM {0} not found.", srpm)

    srpm_name = os.path.basename(srpm_path)

    metadata = {
        "project_id": get_project_id(project),
        "chroots": [],
        "enable_net": False
    }
    data = {
        "srpm": (srpm_name, open(srpm_path), SRPM_MIME_TYPE),
        "metadata": ("", json.dumps(metadata))
    }
    path = urljoin(get_endpoint(), "/api_2/builds")
    response = requests.post(path,
        auth=(config.get("login"), config.get("token")),
        files=data
    )
    if response.status_code != 201:
        raise Error("Build SRPM {0} failed with code {1}.",
            srpm_name, response.status_code)

    return response.headers["location"]


def main_args():
    """Main args."""

    parser = argparse.ArgumentParser()
    parser.add_argument("project", help="COPR project")
    parser.add_argument("srpm", help="SRPM file to build")

    return parser.parse_args()


def exitcode(func):
    """Wrapper for logging any catched exception."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except KeyboardInterrupt:
            return os.EX_TEMPFAIL
        except Exception as e:
            print("Error: {0}".format(e))
            return os.EX_SOFTWARE
        else:
            return os.EX_OK
    return wrapper


@exitcode
def main():
    """Main function."""

    args = main_args()
    config.init()

    build(args.project, args.srpm)
