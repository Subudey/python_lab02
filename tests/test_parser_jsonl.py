from pathlib import Path

import pytest

from streamstats.analysis import analyse_files
from streamstats.errors import InvalidEventError
from streamstats.parsers import ParseStats, jsonl_parser

GOOD = '{"timestamp": "2026-10-20T12:00:00Z", "level": "INFO", "source": "auth", "message": "ok"}\n'
BAD = '{"timestamp": "2026-10-20T12:00:00Z", "level": "BANANA", "source": "auth", "message": "x"}\n'


def test_jsonl_good(tmp_path: Path) -> None:
    """Корректная строка JSONL превращается в одно событие."""

    file = tmp_path / "test.jsonl"
    file.write_text(GOOD, encoding="utf-8")

    events = list(jsonl_parser(str(file), ParseStats()))

    assert len(events) == 1
    assert events[0].source == "auth"


def test_jsonl_bad_line_stop(tmp_path: Path) -> None:
    """Некорректная строка останавливает разбор с InvalidEventError и номером строки."""

    file = tmp_path / "test.jsonl"
    file.write_text(BAD, encoding="utf-8")

    with pytest.raises(InvalidEventError) as info:
        list(jsonl_parser(str(file), ParseStats()))

    assert "строка 1" in str(info.value)


def test_jsonl_bad_line_skipped(tmp_path: Path) -> None:
    """При skip_invalid=True некорректная строка пропускается и учитывается в статистике."""

    file = tmp_path / "test.jsonl"
    file.write_text(BAD, encoding="utf-8")

    stats = ParseStats()

    events = list(jsonl_parser(str(file), stats, skip_invalid=True))

    assert len(events) == 0
    assert stats.skipped == 1


def test_jsonl_empty_file(tmp_path: Path) -> None:
    """Пустой файл не даёт событий и не вызывает ошибок."""

    file = tmp_path / "test.jsonl"
    file.write_text("", encoding="utf-8")

    assert list(jsonl_parser(str(file), ParseStats())) == []


def test_jsonl_some_files(tmp_path: Path) -> None:
    """Анализ нескольких файлов объединяет счётчики и находит первую и последнюю метки времени."""

    file_1 = tmp_path / "test_1.jsonl"
    file_2 = tmp_path / "test_2.jsonl"

    file_1.write_text(
        '{"timestamp": "2026-10-20T10:00:00Z", "level": "ERROR", "source": "db", "message": "x"}\n',
        encoding="utf-8",
    )

    file_2.write_text(
        '{"timestamp": "2026-10-20T13:00:00Z", "level": "INFO", "source": "auth", "message": "x"}\n',
        encoding="utf-8",
    )

    stats = analyse_files([str(file_1), str(file_2)], "jsonl")

    assert stats.total == 2
    assert stats.by_source["db"] == 1
    assert stats.by_source["auth"] == 1
    assert stats.first_timestamp is not None
    assert stats.first_timestamp.hour == 10
    assert stats.last_timestamp is not None
    assert stats.last_timestamp.hour == 13
