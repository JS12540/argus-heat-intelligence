from enum import IntEnum, StrEnum


class Severity(StrEnum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AgentStage(StrEnum):
    DISCOVER = "DISCOVER"
    INVESTIGATE = "INVESTIGATE"
    UNDERSTAND = "UNDERSTAND"
    RESPOND = "RESPOND"
    MONITORING = "MONITORING"


class HeatmapFilterType(IntEnum):
    """The time-range STRUCTURE of a /v1/heatmap request — not real-time/historical/predictive
    (that distinction is just whether start_date is in the past, present, or up to 12h ahead)."""

    SINGLE_HOUR = 1  # requires start_date + start_time
    RANGE_OF_HOURS = 2  # same day; requires start_date + start_time + end_time
    SINGLE_DAY = 3  # requires only start_date (covers 00:00-23:59)
    RANGE_OF_DAYS = 4  # requires start_date + end_date, <= 1 month


class AnalyticType(StrEnum):
    TCM = "tcm"  # temperature snapshot, °C per tile (default)
    EXCEEDANCE = "exceedance"  # total hours above/below threshold per tile
    PERSISTENCE = "persistence"  # longest UNBROKEN run of hours above/below threshold
    TIME_OF_MEASURE = "time_of_measure"  # hour of day (0-23 UTC) the peak temperature occurred
