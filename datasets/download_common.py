import os
import urllib.request


def fetch(url, path):
    """path, downloaded from url first if it isn't there yet."""
    if not os.path.exists(path):
        urllib.request.urlretrieve(url, path + ".part")
        os.replace(path + ".part", path)
    return path
