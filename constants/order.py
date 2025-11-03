from enum import StrEnum


class OrderType(StrEnum):
    """Order types."""

    VSD = "vsd"
    SDIS = "sdis"


class OrderStatus(StrEnum):
    """Order statuses."""

    CREATED = "created"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class UrgencyLevel(StrEnum):
    """Urgency levels."""

    STANDARD = "standard"
    IMMEDIATE = "immediate"
