"""Compatibility wrapper for legacy storage view import path."""

import sys

from ui.storage import storage_view as _storage_view

sys.modules[__name__] = _storage_view
