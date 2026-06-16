"""Hermes execution environment backends.

The lean build ships a single backend — ``local`` — which runs shell commands
directly on the host via the ``BaseEnvironment`` ABC. The terminal_tool.py
factory (_create_environment) selects the backend based on the TERMINAL_ENV
configuration (only ``local`` is supported here).
"""

from tools.environments.base import BaseEnvironment

__all__ = ["BaseEnvironment"]
