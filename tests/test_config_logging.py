import logging

from anpd_monitor.config import Settings
from anpd_monitor.logging_config import configure_logging


def test_settings_from_env_reads_paths_and_numbers(monkeypatch, tmp_path):
    monkeypatch.setenv("ANPD_DATA_DIR", str(tmp_path / "store"))
    monkeypatch.setenv("ANPD_TIMEOUT_SECONDS", "5")
    monkeypatch.setenv("ANPD_MAX_RETRIES", "2")
    settings = Settings.from_env()
    assert settings.data_dir == tmp_path / "store"
    assert settings.timeout_seconds == 5
    assert settings.max_retries == 2


def test_configure_logging_creates_log_directory(tmp_path):
    configure_logging(tmp_path, "INFO")
    logging.getLogger("tests").info("hello")
    assert (tmp_path / "logs" / "anpd_monitor.log").exists()
