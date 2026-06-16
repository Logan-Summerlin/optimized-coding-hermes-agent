import importlib
import logging


terminal_tool_module = importlib.import_module("tools.terminal_tool")


def _clear_terminal_env(monkeypatch):
    """Remove terminal env vars that could affect requirements checks."""
    keys = [
        "TERMINAL_ENV",
        "TERMINAL_LIFETIME_SECONDS",
        "TERMINAL_TIMEOUT",
        "HOME",
        "USERPROFILE",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)


def test_local_terminal_requirements(monkeypatch, caplog):
    """Local backend uses Hermes' own LocalEnvironment wrapper."""
    _clear_terminal_env(monkeypatch)
    monkeypatch.setenv("TERMINAL_ENV", "local")

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True
    assert "Terminal requirements check failed" not in caplog.text


def test_default_terminal_env_is_local(monkeypatch, caplog):
    """No TERMINAL_ENV set falls back to the local backend."""
    _clear_terminal_env(monkeypatch)

    with caplog.at_level(logging.ERROR):
        ok = terminal_tool_module.check_terminal_requirements()

    assert ok is True


def test_non_local_terminal_env_is_rejected(monkeypatch, caplog):
    """The lean build only supports the local backend; anything else fails."""
    _clear_terminal_env(monkeypatch)
    for backend in ("docker", "modal", "ssh", "singularity", "daytona", "unknown-backend"):
        monkeypatch.setenv("TERMINAL_ENV", backend)
        with caplog.at_level(logging.ERROR):
            caplog.clear()
            ok = terminal_tool_module.check_terminal_requirements()
        assert ok is False
        assert any(
            "only supports the 'local' backend" in record.getMessage()
            for record in caplog.records
        )
