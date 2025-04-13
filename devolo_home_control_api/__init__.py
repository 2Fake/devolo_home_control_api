"""the devolo Home Control API."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("devolo_home_control_api")
except PackageNotFoundError:
    # package is not installed - e.g. pulled and run locally
    __version__ = "0.0.0"
