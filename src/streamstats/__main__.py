import logging
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from streamstats.analysis import analyse_files
from streamstats.errors import (
    CLIConfigurationError,
    InvalidEventError,
    StreamStatsError,
)
from streamstats.report import build_report, write_report

app = typer.Typer(help="Потоковый анализатор файлов событий")
EXTENSIONS = {"csv": ".csv", "jsonl": ".jsonl"}


class InputFormat(str, Enum):
    csv = "csv"
    jsonl = "jsonl"


def check_format(paths: list[Path], fmt: str) -> None:
    """Проверить, что расширения файлов соответствуют указанному формату.

    Args:
        paths: Пути к входным файлам.
        fmt: Формат, указанный в --format ("csv" или "jsonl").

    Raises:
        InvalidEventError: Если расширение файла не совпадает с форматом.
    """

    expected = EXTENSIONS[fmt]
    for path in paths:
        if path.suffix.lower() != expected:
            raise InvalidEventError(f"Файл {path} не соответствует формату {fmt}")


@app.callback()
def main() -> None:
    """Настройка логирования приложения."""

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


@app.command()
def analyze(
    inputs: Annotated[
        list[Path],
        typer.Argument(
            exists=True, dir_okay=False, readable=True, help="Входные файлы"
        ),
    ],
    format: Annotated[
        InputFormat, typer.Option("--format", help="Формат входных данных")
    ],
    output: Annotated[Path, typer.Option("--output", help="Место записи JSON отчёта")],
    skip_invalid: Annotated[
        bool, typer.Option("--skip-invalid", help="Пропуск некорректных строк")
    ] = False,
) -> None:
    """Запускает анализ входных файлов и сохранение JSON-отчёта.
    Проверяет параметры CLI, собирает статистику по событиям
    и записывает результат в указанный файл.

    Args:
        inputs: Входные файлы для обработки
        format: Формат файлов
        output: Путь до выходного файла со статистикой
        skip_invalid: Пропускать ли некорректные строки

    Raises:
        StreamStatsError: Ошибки связанные с обработкой входных файлов
        OSError: Ошибки на уровне системы
        UnicodeDecodeError: Ошибки декодировки файла (если не в UTF-8)
    """

    try:
        if output.is_dir():
            raise CLIConfigurationError("--output должен быть файлом")

        check_format(inputs, format.value)
        stats = analyse_files([str(p) for p in inputs], format.value, skip_invalid)
        write_report(build_report(stats), str(output))

    except StreamStatsError as exc:
        typer.echo(f"Ошибка: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    except OSError as exc:
        typer.echo(f"Ошибка ввода-вывода: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    except UnicodeDecodeError as exc:
        typer.echo(f"Ошибка кодировки файла: {exc}", err=True)
        raise typer.Exit(code=2) from exc


if __name__ == "__main__":
    app()
