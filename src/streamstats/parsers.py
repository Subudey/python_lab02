import csv
import json
import logging
from collections.abc import Iterator
from dataclasses import dataclass

from streamstats.errors import InvalidEventError
from streamstats.models import Event, get_event

logger = logging.getLogger(__name__)


@dataclass
class ParseStats:
    skipped: int = 0


def handle_error(
    exc: InvalidEventError,
    path: str,
    line_no: int,
    skip_invalid: bool,
    stats: ParseStats,
) -> None:
    """Обрабатывает ошибку записи с учётом режима пропуска.

    Args:
        exc: Возникшая ошибка при обработке записи.
        path: Путь к файлу.
        line_no: Номер строки с ошибкой.
        skip_invalid: Нужно ли пропустить некорректную запись.
        stats: Статистика обработки записей.

    Raises:
        InvalidEventError: Если пропуск некорректных записей выключен.
    """

    message = f"{path}, строка {line_no}: {exc}"

    if not skip_invalid:
        raise type(exc)(message)

    logger.warning("Пропущена строка: %s", message)
    stats.skipped += 1


def jsonl_to_event(line: str) -> Event:
    """Преобразует строку JSONL в объект Event.

    Args:
        line: Строка с JSON-объектом.

    Returns:
        Проверенный объект события.

    Raises:
        InvalidEventError: Если JSON или данные события некорректны.
    """

    try:
        data = json.loads(line)

    except json.JSONDecodeError:
        raise InvalidEventError("Неправильный формат записей в JSONL файле")

    if not isinstance(data, dict):
        raise InvalidEventError(
            "Полученные из файла данные должны быть JSONL объектами"
        )

    return get_event(data)


def csv_to_event(row: dict[str, object]) -> Event:
    """Преобразует строку CSV в объект Event.

    Args:
        row: Словарь с данными одной строки CSV.

    Returns:
        Проверенный объект события.

    Raises:
        InvalidEventError: Если строка содержит некорректные данные или лишние поля.
    """

    if None in row:
        raise InvalidEventError("В файле обнаружены лишние поля")

    return get_event(row)


def jsonl_parser(
    path: str, stats: ParseStats, skip_invalid: bool = False
) -> Iterator[Event]:
    """Последовательно читает события из JSONL-файла.

    Args:
        path: Путь к входному файлу.
        stats: Статистика обработки записей.
        skip_invalid: Пропускать ли некорректные записи.

    Yields:
        Проверенные события из файла.
    """

    with open(path, "r", encoding="utf-8") as file:
        for line_no, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                event = jsonl_to_event(line)

            except InvalidEventError as exc:
                handle_error(exc, path, line_no, skip_invalid, stats)
                continue

            yield event


def csv_parser(
    path: str, stats: ParseStats, skip_invalid: bool = False
) -> Iterator[Event]:
    """Последовательно читает события из CSV-файла.

    Args:
        path: Путь к входному файлу.
        stats: Статистика обработки записей.
        skip_invalid: Пропускать ли некорректные записи.

    Yields:
        Проверенные события из файла.
    """

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                event = csv_to_event(row)

            except InvalidEventError as exc:
                handle_error(exc, path, reader.line_num, skip_invalid, stats)
                continue

            yield event
