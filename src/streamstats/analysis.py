from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime

from streamstats.errors import UnsupportedFormatError
from streamstats.models import Event, Level
from streamstats.parsers import ParseStats, csv_parser, jsonl_parser


@dataclass
class Stats:
    total: int = 0
    by_level: Counter[str] = field(default_factory=Counter)
    by_source: Counter[str] = field(default_factory=Counter)
    by_error_source: Counter[str] = field(default_factory=Counter)
    first_timestamp: datetime | None = None
    last_timestamp: datetime | None = None
    skipped: int = 0


def analyze(events: Iterable[Event], stats: Stats) -> None:
    """Формирует статистику на основе переданных событий.

    Args:
        events: Последовательность событий для обработки.
        stats: Объект статистики, который нужно сформировать.
    """

    for event in events:
        stats.total += 1
        stats.by_level[event.level.value] += 1
        stats.by_source[event.source] += 1

        if event.level in (Level.ERROR, Level.CRITICAL):
            stats.by_error_source[event.source] += 1

        if stats.first_timestamp is None or event.timestamp < stats.first_timestamp:
            stats.first_timestamp = event.timestamp

        if stats.last_timestamp is None or event.timestamp > stats.last_timestamp:
            stats.last_timestamp = event.timestamp


def analyse_files(paths: list[str], format: str, skip_invalid: bool = False) -> Stats:
    """Формирует статистику событий для нескольких файлов.

    Args:
        paths: Пути к входным файлам.
        format: Формат файлов: csv или jsonl.
        skip_invalid: Пропускать ли некорректные записи.

    Returns:
        Общая статистика по всем обработанным файлам.

    Raises:
        UnsupportedFormatError: Если формат файлов не поддерживается.
    """

    if format == "csv":
        parser = csv_parser

    elif format == "jsonl":
        parser = jsonl_parser

    else:
        raise UnsupportedFormatError(f"Неподдерживаемый формат: {format}")

    stats = Stats()
    parse_stats = ParseStats()

    for path in paths:
        analyze(parser(path, parse_stats, skip_invalid), stats)

    stats.skipped = parse_stats.skipped

    return stats
