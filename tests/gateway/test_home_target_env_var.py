"""Tests for /sethome env-var resolution.

The `/sethome` command writes to a platform's home-target env var. In the lean
build the only messaging platform is Telegram, which follows the
`{PLATFORM}_HOME_CHANNEL` convention, so resolution is a simple uppercase +
`_HOME_CHANNEL` suffix.
"""

from gateway.run import _home_target_env_var, _home_thread_env_var


def test_telegram_home_target_env_var_uses_home_channel():
    assert _home_target_env_var("telegram") == "TELEGRAM_HOME_CHANNEL"


def test_unknown_platform_home_target_env_var_falls_back_to_home_channel():
    assert _home_target_env_var("custom") == "CUSTOM_HOME_CHANNEL"


def test_case_insensitive_platform_name():
    assert _home_target_env_var("Telegram") == "TELEGRAM_HOME_CHANNEL"


def test_home_thread_env_var_uses_home_target_name_plus_thread_id():
    assert _home_thread_env_var("telegram") == "TELEGRAM_HOME_CHANNEL_THREAD_ID"
