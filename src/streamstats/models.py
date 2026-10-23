from collections.abc import Mapping
from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ValidationError, field_validator

from streamstats.errors import InvalidEventError, InvalidTimestampError


class Level(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Event(BaseModel):
    timestamp: datetime
    level: Level
    source: str
    message: str

    @field_validator("timestamp", mode="before")
    @classmethod
    def timestamp_validator(cls, value: object) -> datetime:
        """Проверяет временную метку на валидность и приводит    её к UTC"""

        if not isinstance(value, (str, datetime)):
            raise InvalidTimestampError(
                "Временная метка должна быть string или datetime"
            )

        if isinstance(value, str):
            import re

            TIME_PATTERN = (
                r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})"
            )

            if not re.fullmatch(TIME_PATTERN, value):
                raise InvalidTimestampError(
                    "Неверный формат временной метки (Требуется ISO 8601)"
                )

            try:
                value = datetime.fromisoformat(value)

            except ValueError:
                raise InvalidTimestampError("Некорректная запись временной метки")

        return value.astimezone(tz=UTC)

    @field_validator("source")
    @classmethod
    def source_validator(cls, value: str) -> str:
        """Проверяет источник события на валидность"""

        value = value.strip()

        if not value:
            raise InvalidEventError("Поле source не может быть пустым")

        return value


def get_event(raw: Mapping[str, object]) -> Event:
    """Создаёт и проверяет событие из исходных данных"""

    try:
        return Event.model_validate(raw)

    except ValidationError:
        raise InvalidEventError("Некорректные данные события")
