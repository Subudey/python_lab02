import json
from pathlib import Path

from streamstats.analysis import Stats


def build_report(stats: Stats) -> dict[str, object]:
    """Подготавливает статистику к сохранению в JSON.

    Args:
        stats: Собранная статистика анализа.

    Returns:
        Словарь с общей статистикой, распределением событий,
        источниками ошибок, временными границами и числом пропусков.
    """

    return {
        "total": stats.total,
        "by_level": stats.by_level,
        "by_source": stats.by_source,
        "top_error_sources": [
            {"source": source, "count": count}
            for source, count in stats.by_error_source.most_common(5)
        ],
        "first_timestamp": stats.first_timestamp.isoformat()
        if stats.first_timestamp
        else None,
        "last_timestamp": stats.last_timestamp.isoformat()
        if stats.last_timestamp
        else None,
        "skipped": stats.skipped,
    }


def write_report(report: dict[str, object], path: str) -> None:
    """Записать отчёт в JSON-файл.

    Args:
        report: Данные отчёта.
        path: Путь к выходному файлу.
    """

    text = json.dumps(report, ensure_ascii=False, indent=2)
    Path(path).write_text(text + "\n", encoding="utf-8")
