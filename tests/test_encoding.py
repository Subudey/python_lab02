from pathlib import Path

from streamstats.parsers import ParseStats, jsonl_parser


def test_unicode(tmp_path: Path) -> None:
    """Кириллица в полях события читается без искажений (UTF-8)."""

    file = tmp_path / "test.jsonl"
    file.write_text(
        '{"timestamp": "2026-10-20T12:00:00Z", "level": "INFO", '
        '"source": "база данных", "message": "Пользователь вошёл"}\n',
        encoding="utf-8",
    )

    events = list(jsonl_parser(str(file), ParseStats()))

    assert events[0].source == "база данных"
    assert events[0].message == "Пользователь вошёл"
