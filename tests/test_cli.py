import json
from pathlib import Path

from typer.testing import CliRunner

from streamstats.__main__ import app

runner = CliRunner()


def test_cli_correct(tmp_path: Path) -> None:
    """Команда analyze на корректном файле завершается с кодом 0 и пишет верный JSON-отчёт."""

    src = tmp_path / "in.jsonl"
    out = tmp_path / "report.json"

    src.write_text(
        '{"timestamp": "2026-10-20T12:00:00Z", "level": "INFO", "source": "authorization", "message": "ok"}\n',
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["analyze", str(src), "--format", "jsonl", "--output", str(out)]
    )

    assert result.exit_code == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    assert report["total"] == 1
    assert report["by_source"] == {"authorization": 1}


def test_cli_bad_line(tmp_path: Path) -> None:
    """Команда analyze на файле с некорректной строкой завершается с кодом 2 и не создаёт отчёт."""

    src = tmp_path / "in.jsonl"
    out = tmp_path / "report.json"

    src.write_text(
        '{"timestamp": "2026-10-20T12:00:00Z", "level": "BANANA", "source": "auth", "message": "x"}\n',
        encoding="utf-8",
    )

    result = runner.invoke(
        app, ["analyze", str(src), "--format", "jsonl", "--output", str(out)]
    )

    assert result.exit_code == 2
    assert not out.exists()
