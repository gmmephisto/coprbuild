import ConfigParser
import os

from psys import Error


COPR_CONFIG = os.path.expanduser("~/.config/copr")
"""COPR config with credentials."""

COPR_CONFIG_DATA = {}
"""COPR config data."""


def init(path=COPR_CONFIG):
    """Initializes config data."""

    global COPR_CONFIG_DATA

    if not os.path.exists(path):
        raise Error("COPR config not found.")

    try:
        config = ConfigParser.SafeConfigParser()
        with open(path) as config_file:
            config.readfp(config_file, path)
    except Exception as e:
        raise Error("Error while reading COPR config: {0}", e)

    COPR_CONFIG_DATA = dict(config.items("copr-cli"))


def get(option, default=None):
    """Returns option from config."""

    global COPR_CONFIG_DATA

    return COPR_CONFIG_DATA.get(option, default)
