from anpd_monitor import cli


def test_cli_run_invokes_monitor(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ANPD_DATA_DIR", str(tmp_path))
    called = {}

    def fake_run(settings, days, category, dry_run):
        called.update({"days": days, "category": category, "dry_run": dry_run})
        return "report.md", "report.json"

    monkeypatch.setattr(cli, "configure_logging", lambda data_dir, level: None)
    monkeypatch.setattr(cli, "run_monitor", fake_run)
    assert cli.main(["run", "--dry-run", "--days", "3", "--category", "arco"]) == 0
    assert called == {"days": 3, "category": "arco", "dry_run": True}
    assert "Reporte Markdown: report.md" in capsys.readouterr().out


def test_cli_validate_sources_returns_error_on_failed_source(monkeypatch, tmp_path, capsys):
    monkeypatch.setenv("ANPD_DATA_DIR", str(tmp_path))
    source = cli.COLLECTIONS["arco"]

    class Result:
        candidates_seen = 0
        status = "error"
        errors = ["boom"]

        def __init__(self):
            self.source = source

    monkeypatch.setattr(cli, "configure_logging", lambda data_dir, level: None)
    monkeypatch.setattr(cli, "validate_sources", lambda settings: [Result()])
    assert cli.main(["validate-sources"]) == 1
    assert "arco: error" in capsys.readouterr().out

