class StreamStatsError(Exception):
    """Базовое исключение для потокового анализатора"""


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат файлов"""


class CLIConfigurationError(StreamStatsError):
    """Неверная конфигурация CLI"""


class InvalidEventError(StreamStatsError):
    """Неверный формат записи событий"""


class InvalidTimestampError(InvalidEventError):
    """Неверная запись временной метки"""
