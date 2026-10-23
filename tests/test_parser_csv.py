from pathlib import Path

import pytest

from streamstats.analysis import analyse_files
from streamstats.errors import InvalidEventError
from streamstats.parsers import ParseStats, csv_parser

HEADER = "timestamp,level,source,message\n"
CSV_GOOD = "2026-10-20T12:00:00Z,INFO,auth,ok\n"
CSV_BAD = "2026-10-20T12:00:00Z,BANANA,auth,x\n"


def test_csv_good(tmp_path: Path) -> None:
    """Корректная строка CSV превращается в одно событие."""

    file = tmp_path / "test.csv"
    file.write_text(HEADER + CSV_GOOD, encoding="utf-8")

    events = list(csv_parser(str(file), ParseStats()))

    assert len(events) == 1
    assert events[0].source == "auth"


def test_csv_bad_line_stop(tmp_path: Path) -> None:
    """Некорректная строка останавливает разбор с InvalidEventError и номером строки (с учётом заголовка)."""

    file = tmp_path / "test.csv"
    file.write_text(HEADER + CSV_BAD, encoding="utf-8")

    with pytest.raises(InvalidEventError) as info:
        list(csv_parser(str(file), ParseStats()))

    assert "строка 2" in str(info.value)


def test_csv_bad_line_skipped(tmp_path: Path) -> None:
    """При skip_invalid=True некорректная строка пропускается и учитывается в статистике."""

    file = tmp_path / "test.csv"
    file.write_text(HEADER + CSV_BAD, encoding="utf-8")

    stats = ParseStats()
    events = list(csv_parser(str(file), stats, skip_invalid=True))

    assert len(events) == 0
    assert stats.skipped == 1


def test_csv_empty_file(tmp_path: Path) -> None:
    """Пустой файл не даёт событий и не вызывает ошибок."""

    file = tmp_path / "test.csv"
    file.write_text("", encoding="utf-8")

    assert list(csv_parser(str(file), ParseStats())) == []


def test_csv_some_files(tmp_path: Path) -> None:
    """Анализ нескольких CSV-файлов объединяет счётчики и находит первую и последнюю метки времени."""

    file_1 = tmp_path / "test_1.jsonl"
    file_2 = tmp_path / "test_2.jsonl"

    file_1.write_text(HEADER + "2026-10-20T10:00:00Z,ERROR,db,x\n", encoding="utf-8")
    file_2.write_text(HEADER + "2026-10-20T13:00:00Z,INFO,auth,x\n", encoding="utf-8")

    stats = analyse_files([str(file_1), str(file_2)], "csv")

    assert stats.total == 2
    assert stats.by_source["db"] == 1
    assert stats.by_source["auth"] == 1
    assert stats.first_timestamp is not None
    assert stats.first_timestamp.hour == 10
    assert stats.last_timestamp is not None
    assert stats.last_timestamp.hour == 13
