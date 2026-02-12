"""codex-accounts-switch package."""

from .webapp import create_app
from .version import __version__

__all__ = ["create_app", "__version__"]
